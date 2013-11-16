from django import template

register = template.Library()

@register.inclusion_tag('post.html', takes_context=True)
def display_post(context):
	return {
		'post': context['post'],
		'request': context['request']
	}
