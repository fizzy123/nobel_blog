from django.shortcuts import render
from django.views.generic import ListView
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.utils import timezone

from general.functions import rand_str_gen, parse_post_content

from blog.models import Post, Tag

import pdb

def display(request, post_id=0):
    page = int(request.GET['page']) if request.GET.has_key('page') else 1
    if request.session['logged_in'] if request.session.has_key('logged_in') else False:
        qs = Post.objects.order_by('-pub_date')
    else:
        qs = Post.objects.filter(draft=False).order_by('-pub_date')
    if post_id:
        post_list = [Post.objects.get(pk=post_id).build_post_dict('display')]
    else:
        post_list = []
        for post in qs[(page-1)*10:page*10]:
            post_list.append(post.build_post_dict('display'))
    context = {'posts': post_list}
    if len(qs)/10 != page:
        context['next_page'] = page + 1
    if page != 1:
        context['prev_page'] = page - 1
    return render(request, 'blog/index.html', context)

def add_or_edit(request, post_id=0):
    if request.META['REQUEST_METHOD'] == 'GET':
        if not request.session['logged_in'] if request.session.has_key('logged_in') else True:
            raise Http404
        else:
            if post_id:
                context = {'post': Post.objects.get(pk=post_id).build_post_dict('edit'),
                           'edit': True}
            else:
                context = {}
            return render(request, 'blog/add.html', context)
    elif request.META['REQUEST_METHOD'] == 'POST':
        parsed_content = parse_post_content(request.POST['content'], 'display')
        if request.POST.has_key('tags'):
            tags = request.POST['tags']

        if post_id:
            p = Post.objects.get(pk=post_id)
            p.title = request.POST['title']
            if p.draft == True and not request.POST.has_key('draft'):
                p.pub_date = timezone.now()
            p.draft = request.POST.has_key('draft')
            p.content = parsed_content
            p.set_tags_for_post(tags.split(', '))
        else:
            p = Post.objects.create(title = request.POST['title'],
                     draft = request.POST.has_key('draft'),
                     content = parsed_content)
            if not request.POST.has_key('draft'):
                p.pub_date = timezone.now()
            p.set_tags_for_post(tags.split(', '))
            p.save()
        return HttpResponseRedirect(reverse('blog:index'))

def delete(request):
    if request.session['logged_in'] if request.session.has_key('logged_in') else False:
        p = Post.objects.get(pk=request.POST['pk'])
        tag_list = p.tags.all()
        for tag in tag_list:
            if not len(tag.post_set.all()):
                tag.delete()
        p.delete()
    return HttpResponseRedirect(reverse('blog:index'))
