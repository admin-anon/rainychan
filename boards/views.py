import collections, math, hashlib, operator
from PIL import Image

from django.http import HttpResponseNotFound
from django.shortcuts import render, get_object_or_404, reverse, redirect
from .models import Board, Post, Topic, Reply, BannedIP
from .forms import TopicForm, ReplyForm, DeletionForm, BanForm
from django.template import RequestContext

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
    
def is_banned(request):
    return BannedIP.objects.filter(ip=get_client_ip(request)).count() != 0

def sort_topics(board):
    users_in_threads = {}
    recent_topics = list(Topic.objects.order_by('posted').filter(on_board=board))
    topic_to_date = { topic: topic.posted for topic in recent_topics }

    recent_replies = Reply.objects.order_by('posted').filter(on_board=board)
    for reply in recent_replies:
        if reply.on_topic.from_ip == reply.from_ip:
            continue
        if reply.on_topic in users_in_threads:
            if reply.from_ip in users_in_threads[reply.on_topic]:
                continue
            users_in_threads[reply.on_topic].add(reply.from_ip)
        else:
            users_in_threads[reply.on_topic] = set(reply.from_ip)

        topic_to_date[reply.on_topic] = reply.posted
    
    out = [ k for k, _ in sorted(topic_to_date.items(), key=operator.itemgetter(1))]
    out.reverse()
    return out

def make_reply(new_reply_form, request, board):
    on_topic = get_object_or_404(Topic, on_board=board, post_number=new_reply_form.cleaned_data['to_topic'])

    m = Reply(
        contents=new_reply_form.cleaned_data['contents'],
        attachment=new_reply_form.cleaned_data['attachment'],
        on_board=board,
        on_topic=on_topic,
        from_ip=get_client_ip(request),
    )

    m.password_hash = hashlib.blake2b(new_reply_form.cleaned_data['password'].encode('utf-8')).hexdigest()
            
    if new_reply_form.cleaned_data['tripcode'] != None:
        tripcode_name_code = new_reply_form.cleaned_data['tripcode'].split('#', 1)
        if len(tripcode_name_code) == 2:
            tripcode_name, tripcode_code = tripcode_name_code
            m.tripcode = tripcode_name + '#' + hashlib.blake2b(tripcode_code.encode('utf-8')).hexdigest()[:10]
        else:
            m.tripcode = new_reply_form.cleaned_data['tripcode']

        if request.user.is_authenticated and m.tripcode == 'user':
            m.by_user = request.user
            
        m.save()
        return m

def try_delete(request, board, new_deletion_form):
    post_to_delete = Topic.objects.filter(on_board=board, post_number=new_deletion_form.cleaned_data['post_number'])
    if post_to_delete.count() == 0:
        post_to_delete = Reply.objects.filter(on_board=board, post_number=new_deletion_form.cleaned_data['post_number'])

    if post_to_delete.count() == 0:
        return False
    else:
        post_to_delete = post_to_delete[0]

    if (request.user.is_authenticated and request.user.has_perm('can_delete_posts')) or hashlib.blake2b(new_deletion_form.cleaned_data['password'].encode('utf-8')).hexdigest() == post_to_delete.password_hash:
        post_to_delete.delete()
        return True
    
    return False

def try_ban(request, board, new_ban_form):
    if request.user.is_staff:
        post_number = new_ban_form.cleaned_data['post_number']

        topics = Topic.objects.filter(on_board=board, post_number=post_number)
        replies = Reply.objects.filter(on_board=board, post_number=post_number)

        if topics.count() == 1:
            topic = topics[0]
            BannedIP(ip=topic.from_ip).save()
            topic.banned_for = True
            topic.save_mod()
            return True
        elif replies.count() == 1:
            reply = replies[0]
            BannedIP(ip=reply.from_ip).save()
            reply.banned_for = True
            reply.save_mod()
            return True

    return False

def get_replies(post):
    topics = Topic.objects.filter(on_board=post.on_board)
    replies = Reply.objects.filter(on_board=post.on_board)

    replies_to_post = []
    for other_post in sorted(list(topics) + list(replies), key=operator.attrgetter('post_number')):
        i = 0
        while i < len(other_post.contents):
            tag = '>>' + str(post.post_number)
            found_at = other_post.contents.find(tag, i)
            if found_at == -1:
                break
            next_index = found_at + len(tag)
            if next_index < len(other_post.contents):
                next_char = other_post.contents[found_at + len(tag)]
                if ord(next_char) >= ord('0') and ord(next_char) <= ord('9'):
                    i = next_index + 1
                    continue
            replies_to_post.append(other_post)
            break

    return replies_to_post

def main_view(request):
    if is_banned(request) and not request.user.is_staff:
        return redirect(reverse(banned_view))

    boards = Board.objects.all()

    boards_top_posts = []
    for board in boards:
        topics = sort_topics(board)
        shortened = ""
        if len(topics) > 0:
            shortened = topics[0].contents
            if len(shortened) > 100:
                shortened = shortened[:100] + "..."
        boards_top_posts.append((board, shortened))
    
    recent_posts = sorted(list(Topic.objects.all()) + list(Reply.objects.all()), key=operator.attrgetter('posted'))
    recent_posts.reverse()

    return render(request, 'boards.html', {'boards_top_posts': boards_top_posts, 'recent_posts': recent_posts[:20]})

def board_view(request, board_name, page):
    if is_banned(request) and not request.user.is_staff:
        return redirect(reverse(banned_view))

    board = get_object_or_404(Board, name=board_name)

    posts_per_page = 20

    all_topics = sort_topics(board)

    query = None

    if request.method == 'GET':
        query = request.GET.get('query', None)
        if query:
            new_all_topics = []
            for i, topic in enumerate(all_topics):
                if query.upper() in topic.subject.upper() + topic.contents.upper():
                    new_all_topics.append(all_topics[i])
            all_topics = new_all_topics

    if len(all_topics) / posts_per_page <= page - 1 and page != 1:
        return HttpResponseNotFound()

    posts_to_display = all_topics[(page - 1) * posts_per_page:page * posts_per_page]

    topics_with_replies = []
    for topic in posts_to_display:
        replies = Reply.objects.filter(on_topic=topic).order_by('posted')
        topics_with_replies.append((topic, replies[max(0, replies.count() - 3):]))

    reply_forms = {}
    delete_forms = {}
    ban_forms = {}
    for topic, replies in topics_with_replies:
        reply_forms[topic.post_number] = ReplyForm()
        delete_forms[topic.post_number] = DeletionForm()
        ban_forms[topic.post_number] = BanForm()
        for reply in replies:
            reply_forms[reply.post_number] = ReplyForm()
            delete_forms[reply.post_number] = DeletionForm()
            ban_forms[reply.post_number] = BanForm()

    post_form = TopicForm()

    if request.method == 'POST':
        if 'topicform_identifier' in request.POST:
            new_topic_form = TopicForm(request.POST, request.FILES)

            if new_topic_form.is_valid():
                m = Topic(
                    subject=new_topic_form.cleaned_data['subject'],
                    contents=new_topic_form.cleaned_data['contents'],
                    attachment=new_topic_form.cleaned_data['attachment'],
                    on_board=board,
                    from_ip=get_client_ip(request),
                )

                m.password_hash = hashlib.blake2b(new_topic_form.cleaned_data['password'].encode('utf-8')).hexdigest()
                
                if new_topic_form.cleaned_data['tripcode'] != None:
                    tripcode_name_code = new_topic_form.cleaned_data['tripcode'].split('#', 1)
                    if len(tripcode_name_code) == 2:
                        tripcode_name, tripcode_code = tripcode_name_code
                        m.tripcode = tripcode_name + '#' + hashlib.blake2b(tripcode_code.encode('utf-8')).hexdigest()[:10]
                    else:
                        m.tripcode = new_topic_form.cleaned_data['tripcode']

                if request.user.is_authenticated and m.tripcode == 'user':
                    m.by_user = request.user

                m.save()
                return redirect(reverse(topic_view, args=[board_name, m.post_number]))

            post_form = new_topic_form
        elif 'replyform_identifier' in request.POST:
            new_reply_form = ReplyForm(request.POST, request.FILES)

            if new_reply_form.is_valid():
                m = make_reply(new_reply_form, request, board)

                return redirect(reverse(topic_view, args=[board_name, m.on_topic.post_number]) + '#' + str(m.post_number))
            else:
                if 'post_number' in new_reply_form.cleaned_data:
                    reply_forms[new_reply_form.cleaned_data['post_number']] = new_reply_form
                    this_reply_set = Reply.objects.filter(post_number=new_reply_form.cleaned_data['post_number'])
                    this_topic_set = Topic.objects.filter(post_number=new_reply_form.cleaned_data['post_number'])
                    if len(this_reply_set) == 1:
                        this_reply = this_reply_set[0]
                        for i, (topic, replies) in enumerate(topics_with_replies):
                            if topic == this_reply.on_topic:
                                if this_reply not in replies:
                                    topics_with_replies[i][1].insert(0, this_reply)
                                    break
                    if len(this_topic_set) == 0:
                        return HttpResponseNotFound()
                else:
                    return HttpResponseNotFound()
        elif 'deleteform_identifier' in request.POST:
            new_deletion_form = DeletionForm(request.POST)

            success = False
            if new_deletion_form.is_valid():
                success = try_delete(request, board, new_deletion_form)

                if success:
                    return redirect(reverse(board_view, args=[board_name, page]))
                else:
                    new_deletion_form.add_error('password', 'Incorrect password')

            if not success:
                if 'post_number' in new_deletion_form.cleaned_data:
                    delete_forms[new_deletion_form.cleaned_data['post_number']] = new_deletion_form
                    this_reply_set = Reply.objects.filter(post_number=new_deletion_form.cleaned_data['post_number'])
                    this_topic_set = Topic.objects.filter(post_number=new_deletion_form.cleaned_data['post_number'])
                    if len(this_reply_set) == 1:
                        this_reply = this_reply_set[0]
                        for i, (topic, replies) in enumerate(topics_with_replies):
                            if topic == this_reply.on_topic:
                                if this_reply not in replies:
                                    topics_with_replies[i][1].insert(0, this_reply)
                                    break
                    elif len(this_topic_set) == 0:
                        return HttpResponseNotFound()
                else:
                    return HttpResponseNotFound()
        elif 'banform_identifier' in request.POST:
            new_ban_form = BanForm(request.POST)

            success = False
            if new_ban_form.is_valid():
                success = try_ban(request, board, new_ban_form)
            
            if not success:
                if 'post_number' in new_ban_form.cleaned_data:
                    ban_forms[new_ban_form.cleaned_data['post_number']] = new_ban_form
                    this_reply_set = Reply.objects.filter(post_number=new_ban_form.cleaned_data['post_number'])
                    this_topic_set = Topic.objects.filter(post_number=new_ban_form.cleaned_data['post_number'])
                    if len(this_reply_set) == 1:
                        this_reply = this_reply_set[0]
                        for i, (topic, replies) in enumerate(topics_with_replies):
                            if topic == this_reply.on_topic:
                                if this_reply not in replies:
                                    topics_with_replies[i][1].insert(0, this_reply)
                                    break
                    elif len(this_topic_set) == 0:
                        return HttpResponseNotFound()
                else:
                    return HttpResponseNotFound()

    topics_replies_forms = []
    for topic, replies in topics_with_replies:
        replies_with_forms = []
        for reply in replies:
            replies_with_forms.append((reply, reply_forms[reply.post_number], delete_forms[reply.post_number], ban_forms[reply.post_number], get_replies(reply)))
        topics_replies_forms.append((topic, reply_forms[topic.post_number], delete_forms[topic.post_number], ban_forms[topic.post_number], get_replies(topic), replies_with_forms))

    last = max(1, math.ceil(len(all_topics) / posts_per_page))
    return render(request, 'board.html', {'board': board, 'topics_replies_forms': topics_replies_forms, 'post_form': post_form, 'page': page, 'prev': page - 1, 'next': page + 1, 'last': last, 'query': query})

def board_view_no_page(request, board_name):
    return board_view(request, board_name, 1)

def topic_view(request, board_name, post_number):
    if is_banned(request) and not request.user.is_staff:
        return redirect(reverse(banned_view))

    board = get_object_or_404(Board, name=board_name)
    topic = get_object_or_404(Topic, on_board=board, post_number=post_number)

    replies = Reply.objects.filter(on_topic=topic).order_by('post_number')

    reply_forms = {topic.post_number: ReplyForm()}
    delete_forms = {topic.post_number: DeletionForm()}
    ban_forms = {topic.post_number: BanForm()}
    for reply in replies:
        reply_forms[reply.post_number] = ReplyForm()
        delete_forms[reply.post_number] = DeletionForm()
        ban_forms[reply.post_number] = BanForm()

    if request.method == 'POST':
        if 'replyform_identifier' in request.POST:
            new_reply_form = ReplyForm(request.POST, request.FILES)

            if new_reply_form.is_valid():
                m = make_reply(new_reply_form, request, board)

                return redirect(reverse(topic_view, args=[board_name, m.on_topic.post_number]) + '#' + str(m.post_number))
            else:
                if 'post_number' in new_reply_form.cleaned_data:
                    reply_forms[new_reply_form.cleaned_data['post_number']] = new_reply_form
                else:
                    return HttpResponseNotFound()
        elif 'deleteform_identifier' in request.POST:
            new_deletion_form = DeletionForm(request.POST)

            if new_deletion_form.is_valid():
                success = try_delete(request, board, new_deletion_form)

                if success:
                    if new_deletion_form.cleaned_data['post_number'] == post_number:
                        return redirect(reverse(board_view_no_page, args=[board_name]))
                    else:
                        return redirect(reverse(topic_view, args=[board_name, post_number]))
                else:
                    new_deletion_form.add_error('password', 'Incorrect password')
                    delete_forms[new_deletion_form.cleaned_data['post_number']] = new_deletion_form
            else:
                if 'post_number' in new_deletion_form.cleaned_data:
                    delete_forms[new_deletion_form.cleaned_data['post_number']] = new_deletion_form
                else:
                    return HttpResponseNotFound()
        elif 'banform_identifier' in request.POST:
            new_ban_form = BanForm(request.POST, request.FILES)

            if new_ban_form.is_valid():
                success = try_ban(request, board, new_ban_form)

                if not success:
                    return HttpResponseNotFound()
                
                if success and new_ban_form.cleaned_data['post_number'] == topic.post_number:
                    return redirect(reverse(board_view_no_page, args=[board.name]))
            else:
                if 'post_number' in new_ban_form.cleaned_data:
                    ban_forms[new_ban_form.cleaned_data['post_number']] = new_ban_form
                else:
                    return HttpResponseNotFound()

    replies_with_forms = []
    for reply in replies:
        replies_with_forms.append((reply, reply_forms[reply.post_number], delete_forms[reply.post_number], ban_forms[reply.post_number], get_replies(reply)))
    
    return render(request, 'topic_page.html', {'board': board, 'topic': topic, 'topic_reply_form': reply_forms[topic.post_number], 'topic_delete_form': delete_forms[topic.post_number], 'topic_ban_form': ban_forms[topic.post_number], 'mentioned_in': get_replies(topic), 'replies_with_forms': replies_with_forms})

def banned_view(request):
    return render(request, 'banned.html')

def handler404(request, *args, **kwargs):
    response = render(request, '404.html')
    response.status_code = 404
    return response

def handler500(request, *args, **kwargs):
    response = render(request, '500.html')
    response.status_code = 500
    return response