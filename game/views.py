import json
import urllib.parse

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib import messages
from django.core.cache import cache
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from .game_handlers import (
    ColorTaken,
    GameFisnished,
    GameResulted,
    GameStarted,
    NameTaken,
    add_player_to_game,
    creat_game,
    generate_game_id,
    get_game_results,
    restart_game,
)

channel_layer = get_channel_layer()
# Create your views here.


def home(request):
    context = {}
    return render(request, "game/home.html", context=context)


def join(request):
    context = {}
    if request.method == "POST":
        game_id = request.POST.get("game")
        # if game_id.strip() == "":
        #     game_id = generate_game_id()
        name = request.POST.get("name")
        color = request.POST.get("color")
        game = cache.get(f"game:{game_id}")

        if game:
            try:
                add_player_to_game(game, name, color)
                cache.set(f"game:{game_id}", game)
            except NameTaken:
                messages.add_message(
                    request, messages.ERROR, "The (NAME) is taken, pick other name"
                )
                return HttpResponseRedirect(request.path_info)
            except GameStarted:
                messages.add_message(request, messages.ERROR, "The Game is started")
                return HttpResponseRedirect(request.path_info)
            except ColorTaken:
                messages.add_message(
                    request, messages.ERROR, "The (COLRO) is taken, pick other name"
                )
                return HttpResponseRedirect(request.path_info)

        else:
            game = creat_game(game_id)
            add_player_to_game(game, name, color)
            cache.set(f"game:{game_id}", game)
        context["game_id"] = game_id
        context["name"] = name
        context["color"] = color
        url = "{}?{}".format(reverse("game:game"), urllib.parse.urlencode(context))
        return redirect(url)
    return render(request, "game/join.html")


def game(request):
    context = {}
    context["name"] = request.GET.get("name")
    context["game_id"] = request.GET.get("game_id")
    context["color"] = request.GET.get("color")
    return render(request, "game/game.html", context=context)


def get_result(request):
    print("get result 1")
    game_id = request.GET.get("game_id")
    game = cache.get(f"game:{game_id}")
    try:
        game_results = get_game_results(game)
        async_to_sync(channel_layer.group_send)(
            str(game_id), {"type": "Send_Results", "data": game_results}
        )
        game_restarted = restart_game(game)
        cache.set(f"game:{game_id}", game_restarted)
    except GameResulted:
        pass
    print("send json respons workd 6")

    return JsonResponse({"data": "nothing 7"})
