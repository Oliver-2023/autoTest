# Copyright (c) 2010 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


# DESCRIPTION :
#
# Select the keyboard type, and write to VPD.


import gtk
import pango
import sys
import utils

from gtk import gdk

from autotest_lib.client.bin import factory
from autotest_lib.client.bin import factory_ui_lib as ful
from autotest_lib.client.bin import test
from autotest_lib.client.common_lib import error

# Mapping between menu choice and KB.
# Ref: http://git.chromium.org/gitweb/?\
#  p=chromiumos/platform/assets.git;a=blob;f=input_methods/whitelist.txt;hb=HEAD
# Ref: http://google.com/codesearch/p?hl=en#\
#  OAMlx_jo-ck/src/ui/base/l10n/l10n_util.cc\
#  &q=kAcceptLanguageList&exact_package=chromium&sa=N&cd=1&ct=rc
kb_map = (
  ('', '', 'None (ignore)'),
  ('xkb:us::eng',           'en-US',      'US - English'),
  ('xkb:gb:extd:eng',       'en-GB',      'United Kingdom - English'),
  ('xkb:fr::fra',           'fr-FR',      'France - French'),
  ('xkb:de::ger',           'de-DE',      'Germany - German'),
  ('xkb:it::ita',           'it-IT',      'Italy - Italian'),
  ('xkb:es::spa',           'es',         'Spain - Spanish'),
  ('xkb:nl::nld',           'nl',         'Netherlands - Dutch'),

  # Uncomment layouts you need from following list.

  #('xkb:be::nld',           'nl',         'Belgium - Dutch'),
  #('xkb:be::fra',           'fr',         'Belgium - French'),
  #('xkb:ca::fra',           'fr-CA',      'Canada - French'),
  #('xkb:ch:fr:fra',         'fr-CH',      'Switzerland - French'),
  #('xkb:de:neo:ger',        'de',         'Germany - Neo 2'),
  #('xkb:be::ger',           'de',         'Belgium - German'),
  #('xkb:ch::ger',           'de-CH',      'Switzerland - German'),
  #('xkb:jp::jpn',           'ja',         'Japan - Japanese'),
  #('xkb:ru::rus',           'ru',         'Russia - Russian'),
  #('xkb:ru:phonetic:rus',   'ru',         'Russia - Phonetic - Russian'),
  #('xkb:us:altgr-intl:eng', 'en-US',      'US - Extended (AltGr) - English'),
  #('xkb:us:intl:eng',       'en-US',      'US - International - English'),
  #('xkb:us:dvorak:eng',     'en-US',      'US - Dvorak - English'),
  #('xkb:us:colemak:eng',    'en-US',      'US - Colemak - English'),
  #('xkb:br::por',           'pt-BR',      'Brazil - Portuguese'),
  #('xkb:bg::bul',           'bg',         'Bulgaria - Bulgarian'),
  #('xkb:bg:phonetic:bul',   'bg',         'Bulgaria - Phonetic - Bulgarian'),
  #('xkb:ca:eng:eng',        'ca',         'Canada - English'),
  #('xkb:cz::cze',           'cs',         'Czech Republic - Czech'),
  #('xkb:ee::est',           'et',         'Estonia - Estonian'),
  #('xkb:es:cat:cat',        'ca',         'Spain - Catalan'),
  #('xkb:dk::dan',           'da',         'Denmark - Danish'),
  #('xkb:gr::gre',           'el',         'Greece - Greek'),
  #('xkb:il::heb',           'iw',         'Israel - Hebrew'),
  #('xkb:kr:kr104:kor',      'ko',   'Korea - Korean (101/104 key Compatible)'),
  #('xkb:latam::spa',        'es-419',     'Latin America - Spanish'),
  #('xkb:lt::lit',           'lt',         'Lithuania - Lithuanian'),
  #('xkb:lv:apostrophe:lav', 'lv',     'Latvia - Latvian (Apostrophe variant)'),
  #('xkb:hr::scr',           'hr',         'Croatia - Croatian'),
  #('xkb:gb:dvorak:eng',     'en-GB',      'United Kingdom - Dvorak - English'),
  #('xkb:fi::fin',           'fi',         'Finland - Finnish'),
  #('xkb:hu::hun',           'hu',         'Hungary - Hungarian'),
  #('xkb:no::nob',           'no',         'Norway - Norwegian Bokmal'),
  #('xkb:pl::pol',           'pl',         'Poland - Polish'),
  #('xkb:pt::por',           'pt-PT',      'Portugal - Portuguese'),
  #('xkb:ro::rum',           'ro',         'Romania - Romanian'),
  #('xkb:se::swe',           'sv',         'Sweden - Swedish'),
  #('xkb:sk::slo',           'sk',         'Slovakia - Slovak'),
  #('xkb:si::slv',           'sl',         'Slovenia - Slovene (Slovenian)'),
  #('xkb:rs::srp',           'sr',         'Serbia - Serbian'),
  #('xkb:tr::tur',           'tr',         'Turkey - Turkish'),
  #('xkb:ua::ukr',           'uk',         'Ukraine - Ukrainian'),
)

assert len(kb_map) <= 10, "Currently layouts must be less than 10."

class factory_SelectKeyboard(test.test):
    version = 2

    def write_kb(self, kb):
        cmd = ('vpd -i RO_VPD -s "initial_locale"="%s" '
               '-s "keyboard_layout"="%s"' % (kb[1], kb[0]))
        utils.system_output(cmd)

    def key_release_callback(self, widget, event):
        if self.writing:
            return True

        char = chr(event.keyval) if event.keyval in range(32,127) else  None
        factory.log('key_release %s(%s)' % (event.keyval, char))
        try:
            select = int(char)
        except ValueError:
            factory.log('Need a number.')
            return True

        if select < 0 or select >= len(kb_map):
            factory.log('Invalid selection: %d' % select)
            return True

        data = kb_map[select]
        factory.log('Selected: %s' % ', '.join(data))
        if data[0]:
            self.label.set_text('Writing keyboard layout:\n<%s: %s - %s>\n'
                                'Please wait... (may take >10s)' %
                                (data[2], data[0], data[1]))
            self.writing = True
            gtk.main_iteration(False)  # try to update screen
            self.write_kb(data)
        gtk.main_quit()
        return True

    def register_callbacks(self, window):
        window.connect('key-release-event', self.key_release_callback)
        window.add_events(gdk.KEY_RELEASE_MASK)

    def run_once(self):

        factory.log('%s run_once' % self.__class__)

        # Message to display.
        msg = ('Choose a keyboard:\n' + "\n".join(
                ['%s) %s - %s (%s)' % (index, data[2], data[0], data[1])
                 for (index, data) in enumerate(kb_map)]))

        self.label = ful.make_label(msg)
        self.writing = False

        test_widget = gtk.EventBox()
        test_widget.modify_bg(gtk.STATE_NORMAL, ful.BLACK)
        test_widget.add(self.label)

        ful.run_test_widget(self.job, test_widget,
            window_registration_callback=self.register_callbacks)

        factory.log('%s run_once finished' % repr(self.__class__))
