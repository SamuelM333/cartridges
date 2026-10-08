# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2025 kramo

from gettext import gettext as _
from typing import Any

from gi.repository import GObject, Gtk

from cartridges import SETTINGS
from cartridges.config import PREFIX
from cartridges.games import Game

from .collections import CollectionActions, CollectionsBox
from .cover import Cover  # noqa: F401
from .games import GameActions


@Gtk.Template(resource_path=f"{PREFIX}/game-item.ui")
class GameItem(Gtk.Box):
    """A game in the grid."""

    __gtype_name__ = __qualname__

    motion: Gtk.EventControllerMotion = Gtk.Template.Child()
    options: Gtk.MenuButton = Gtk.Template.Child()
    collections_box: CollectionsBox = Gtk.Template.Child()
    action_button: Gtk.Button = Gtk.Template.Child()
    title_label: Gtk.Label = Gtk.Template.Child()

    game_actions: GameActions = Gtk.Template.Child()
    collection_actions: CollectionActions = Gtk.Template.Child()

    game = GObject.Property(type=Game)
    position = GObject.Property(type=int)

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

        self.insert_action_group("game", self.game_actions)
        self.insert_action_group("collection", self.collection_actions)
        self._reveal_buttons()

        SETTINGS.connect("changed::cover-launches-game", self._update_action_button)
        self._update_action_button()

        self._cover_handler: tuple[Game, int] | None = None
        SETTINGS.connect("changed::show-game-titles", self._update_title)
        self.connect("notify::game", self._watch_cover)
        self._watch_cover()

    def _watch_cover(self, *_args: Any) -> None:
        # Games without a cover keep their title, so follow cover changes
        if self._cover_handler:
            old_game, handler = self._cover_handler
            old_game.disconnect(handler)
            self._cover_handler = None

        if self.game:
            self._cover_handler = (
                self.game,
                self.game.connect("notify::cover", self._update_title),
            )

        self._update_title()

    def _update_title(self, *_args: Any) -> None:
        self.title_label.set_visible(
            SETTINGS.get_boolean("show-game-titles")
            or self.game is None
            or self.game.cover is None
        )

    def _update_action_button(self, *_args: Any) -> None:
        if SETTINGS.get_boolean("cover-launches-game"):
            self.action_button.set_icon_name("help-about-symbolic")
            self.action_button.set_tooltip_text(_("Details"))
            self.action_button.set_action_name("game.details")
        else:
            self.action_button.set_icon_name("media-playback-start-symbolic")
            self.action_button.set_tooltip_text(_("Play"))
            self.action_button.set_action_name("game.play")

    @Gtk.Template.Callback()
    def _reveal_buttons(self, *_args: Any) -> None:
        contains_pointer = self.motion.props.contains_pointer
        for widget, reveal in (
            (self.action_button, contains_pointer),
            (self.options, contains_pointer or self.options.props.active),
        ):
            widget.props.can_focus = widget.props.can_target = reveal
            (widget.remove_css_class if reveal else widget.add_css_class)("hidden")

    @Gtk.Template.Callback()
    def _setup_collections(self, button: Gtk.MenuButton, *_args):
        if button.props.active:
            self.collections_box.build()
        else:
            self.collections_box.finish()
