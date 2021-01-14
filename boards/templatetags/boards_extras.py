from django import template

register = template.Library()

from django import template
from django.template.defaultfilters import stringfilter
from django.shortcuts import reverse
from boards import views, models

@register.filter
def make_links(value, board):
    out = ''

    i = 0
    while i < len(value) - 2:
        if ((i  >= 4 and value[i - 4:i] != '&gt;') or i < 4) and value[i:i + 8] == '&gt;&gt;' and value[i + 8:i + 12] != '&gt;':
            end = i + 8
            for j in range(i + 8, len(value)):
                if ord(value[j]) >= ord('0') and ord(value[j]) <= ord('9'):
                    end += 1
                else:
                    break
            post_number = int(value[i + 8:end])
            topics = models.Topic.objects.filter(on_board=board, post_number=post_number)
            if topics.count() != 1:
                replies = models.Reply.objects.filter(on_board=board, post_number=post_number)
                if replies.count() != 1:
                    out += value[i:end]
                else:
                    reply = replies[0]
                    out += '<a href="' + reverse(views.topic_view, args=[reply.on_board.name, reply.on_topic.post_number]) + '#' + value[i + 8:end] + '">' + value[i:end] + "</a>"
            else:
                topic = topics[0]
                out += '<a href="' + reverse(views.topic_view, args=[topic.on_board.name, topic.post_number]) + '">' + value[i:end] + "</a>"
            i = end
        else:
            out += value[i]
            i += 1
    out += value[i:]

    out2 = ''

    i = 0
    while i < len(out) - 3:
        if out[i:i + 13] == '&gt;&gt;&gt;/':
            end = i + 13
            for j in range(i + 13, len(out)):
                if out[j] == '/':
                    end = j + 1
            out2 += '<a href="' + reverse(views.board_view_no_page, args=[out[i + 13:end - 1]]) + '">' + out[i:end] + "</a>"
            i = end
        else:
            out2 += out[i]
            i += 1
    out2 += out[i:]

    return out2

@register.filter
def convert_number_to_link(value, board):
    return make_links('&gt;&gt;' + str(value), board)

@register.filter
def is_topic(value):
    if isinstance(value, models.Topic):
        return True

    return False

@register.filter
@stringfilter
def shorten(value):
    if len(value) > 60:
        return value[:60] + "..."
    return value