# tmpurl.py  A python script for weechat to shorten URLs by generating JavaScript redirects (seriously)
# Copyright (C) <2016>  <sudokode@gmail.com>
# 
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
# 
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
# 
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

SCRIPT_NAME = "tmpurl"
SCRIPT_AUTHOR = "sudokode <sudokode@gmail.com>"
SCRIPT_VERSION = "1.0.0"
SCRIPT_LICENSE = "GPL3"
SCRIPT_DESC = "Create temporary files with JavaScript redirects for long URLs"

import weechat
import os, re

options = {
        "color": "red",
        "min_length": "60",
        "max_history": "42",
        "dirpath": "/tmp/url",
        "shorten_own": "off",
}

option_desc = {
        "color": 'the color of the output URL (default: "red")',
        "min_length": 'the minimum length a URL must be to get shortened (default: "60")',
        "max_history": 'the maximum number of files to be created before restarting the count (default: "42")',
        "dirpath": 'the directory path where the files should be stored (default: "/tmp/url")',
        "shorten_own": 'shorten your own URLs (default: "off")',
}

# template for HTML files
TEMPLATE = "\
<!DOCTYPE html>\n \
<html>\n \
  <head>\n \
    <script type='text/javascript'>\n \
      window.location.assign('{}')\n \
    </script>\n \
  </head>\n \
  <body> \n \
    <h3>Redirecting...</h3>\n \
  </body>\n \
</html>\n"

# history counter
counter = 0

def tmpurl_config_cb(data, long_option, value):
    global options

    # find the actual option name
    pos = long_option.rfind('.')
    if pos > 0:
        option = long_option[pos+1]
        if option in options:
            options[option] = value

    return weechat.WEECHAT_RC_OK

def tmpurl_print_cb(data, buffer, time, tags, displayed, highlight, prefix, message):
    global options

    urls = re.findall("[A-Za-z0-9\.]+://[^ ]+", message)
    for url in urls:
        if len(url) >= int(options["min_length"]):
            file_path = create_tmp(buffer, prefix, url)
            if file_path:
                weechat.prnt(buffer, "{}{}{}".format(weechat.color(options["color"]), file_path, weechat.color("reset")))
            else:
                weechat.prnt(buffer, "{}error creating tmpurl{}".format(weechat.color(options["color"]), weechat.color("reset")))

    return weechat.WEECHAT_RC_OK

def get_nick(buffer):
    buf = weechat.infolist_get("buffer", buffer, "")
    weechat.infolist_next(buf)
    server = weechat.infolist_string(buf, "localvar_value_00000")
    weechat.infolist_free(buf)
    return weechat.info_get("irc_nick", server)

def is_own(buffer, prefix):
    sender = prefix
    if not weechat.info_get("irc_is_nick", sender) or weechat.info_get("irc_is_nick", sender):
        sender = sender[1:]
    if not weechat.info_get("irc_is_nick", sender):
        return False

    nick = get_nick(buffer)
    if nick == sender:
        return True
    else:
        return False

def create_tmp(buffer, prefix, url):
    global options
    global counter

    if options["shorten_own"] == "off":
        if is_own(buffer, prefix):
            return None

    #weechat.prnt(buffer, "{} <> {}".format(len(url), url))
    file_path = "{}/{}.html".format(options["dirpath"], counter)
    try:
        if not os.path.exists((options["dirpath"])):
            os.makedirs(options["dirpath"])

        f = open(file_path, "w")
        f.write(TEMPLATE.format(url))
        f.close()
    except:
        weechat.prnt(buffer, "error opening/writing")
        return None
    else:
        if counter < int(options["max_history"]):
            counter += 1
        else:
            counter = 0
        file_path = "file://{}".format(file_path)
        return file_path

if __name__ == "__main__":
    if weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESC, "", ""):
        # set default options
        for option, value in options.iteritems():
            if not weechat.config_is_set_plugin(option):
                weechat.config_set_plugin(option, value)
            else:
                options[option] = weechat.config_get_plugin(option)

        # set option descriptions
        for option, desc in option_desc.iteritems():
            weechat.config_set_desc_plugin(option, desc)

        # detect config changes
        weechat.hook_config("plugins.var.python.{}.*".format(SCRIPT_NAME), "tmpurl_config_cb", "")

        # catch URLs in buffers
        weechat.hook_print("", "", "://", 1, "tmpurl_print_cb", "")
