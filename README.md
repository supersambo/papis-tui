# papis-tui
<sup>**!!! papis-tui is at an highly experimental stage. I have not tested this on any other machine than my own and only using my personal papis configuration and library. Please proceed with caution, papis-tui can delete documents in your database. Always have a backup in place !!!**<sup>

papis-tui aims to be(come) a highly customizable general purpose **t**erminal **u**ser **i**nterface for the [papis](https://github.com/papis/papis) bibliography manager.

Be aware that `papis-tui` is not a full blown bibliography manager but only a "frontend" for your existing [papis](https://github.com/papis/papis) database!

[![image](https://github.com/supersambo/repo_pics/blob/main/papis-tui_overview.jpg?raw=true)](https://www.youtube.com/watch?v=O9VQ-W9cza0)
<sup>The above image and [screencast](https://www.youtube.com/watch?v=O9VQ-W9cza0) were created with the [this configuration](https://gist.github.com/supersambo/e90c034393fee09842c7d108b6ff00cc) in place</sup>


# Installation
Install the github version via pip:
```
pip install git+https://github.com/supersambo/papis-tui.git@main
```

**Note:** If you install papis and papistui using `pipx`, you have to inject papistui into the `venv` where papis lives in order for it to register papistui as picker:
```
pipx inject papis papistui
```

# Quickstart
Once installed, you should be able to start papis-tui from the command line as:

```
papis-tui
```

...or as a papis command:

```
papis tui
```

If there is no configuration file in place, papis-tui will offer to create a minimal default configuration file. All available commands as well as those commands mapped to certain keys can be looked up from within papis-tui in the help menu by typing `:help`. Descriptions and available options for individual commands can be found by adding the '--help' flag in the command mode. For instance `:open --help` will bring up the help message for the `open` command.

# Features
- highly customizable
- choose between two display styles (table/multiline)
- open, tag, remove, edit documents
- search documents
- sort documents
- vim/neovim connection
- in app help menu
- ...

# Configuration
`papis-tui` is configured via a YAML configuration file in your papis config folder (something like `~/.config/papis/papistui.yaml`). Configuration options are not yet documented extensively. However when starting papis-tui without a config file in place, it will offer to create a default config file, which is a good starting point to tinker around. Alternatively, you can also check out config file used for the screencast above [here](https://gist.github.com/supersambo/e90c034393fee09842c7d108b6ff00cc).

## Configure display styles
`papis-tui` offers two different styles for displaying information about the documents in your library. 'multiline' mimics papis native tui and displays information about documents on several lines, whereas 'table' shows information in columns on one line per document. I personally prefer 'multiline', which is why 'table'-style is somewhat neglected. The default display style can be configured in the `documentlist` section of your config file like this:

``` yaml
documentlist:
  defaultstyle: multiline #or table
```

When the tui is running you can switch between multiline- and table-style by typing `:toggle_style`.

Similar to papis' native tui everything that is enclosed in curly brackets will get interpreted, so that you can display a documents title like this `{doc.html_escape['title']}`. The only difference is that `papis-tui` evaluates strings in curly brackets as python code, meaning that `{str(1 + 1)}` is a valid expression that will result in `2`.

### Multiline
The multiline display style can take a number of lines that display information about documents using a type of pseudo htmly markup language. Colors and style highly depend on your terminal settings and fonts used. Colors can be used as follows: `<bg>` (background), `<black`, `<red>` `<green>` `<yellow>` `<blue>` `<magenta>` `<cyan>` `<white>` and must always be closed in order to be rendered correctly `<white>text</white>`. Colors can be combined using an underscore in order to control fore- and background e.g. `<red_green>` (`<foreground_background>`). Font variations such as `bold`, `italic` and `underline` can also be used and combined in nested forms:

```html

<red><bold>title:</bold>{doc.html_escape['title']}</red>

```

Content and style is defined in the documentlist->multilinestyle section of your config file in `rows`, which takes a list of strings to be interpreted.

```yaml
documentlist:
  multilinestyle:
    rows:
      - "<red><bold>({doc.html_escape['year']})</bold> {doc.html_escape['author']}</red>"
      - "{doc.html_escape['title']}"
      - "{doc.foreach('tags', '<cyan>*{}*<cyan>', split = ', ', sep = '   ')}"
```

![image](https://github.com/supersambo/repo_pics/blob/main/multiline.jpg?raw=true)

`papis-tui` injects a few additional methods into the papis Document class in order to display content conveniently. One example of this is used on the last line above. `docs.foreach` allows to display elements of a list enclosed in a specific style while specifying a separator `sep` (strings can be split into lists using the `split` argument).

### Tablestyle
Table is less customizable in terms of styling. Pseudo html styling is not parsed in this case. Rather, one can choose styling attributes for the header (`headerstyle`), selected rows (`cursorrowstyle`), non selected rows (`rowstyle`) and the separator to be placed between columns. Still, style attributes can be combined using the pipe operator (e.g. `bold|red_green|underline`).

Table style is defined columnwise, where each column entry takes three inputs `content` (what is displayed on each row per document), `header` (column title) and a fixed `width` for each column. Checkout the self-explanatory example below:

```yaml
documentlist:
  tablestyle:
    columns:
    - content: '{doc.html_escape["ref"]}'
      header: Ref
      width: 15
    - content: '{doc.html_escape["author"]}'
      header: Author
      width: 30
    - content: '{doc.html_escape["year"]}'
      header: Year
      width: 4
    - content: '{doc.html_escape["title"]}'
      header: Title
      width: 400
    cursorrowstyle: black_white
    headerstyle: underline|bold
    rowstyle: white_bg
    separator: " \u2502 "
    defaultsort: "time-added-"
```

![image](https://github.com/supersambo/repo_pics/blob/main/tablestyle.jpg?raw=true)

## Keymappings
Any command including its arguments can be mapped to a key or key combination . Commands can be mapped to case sensitive single keys (e.g. `j`,`k`, `l`, `J`, `K`, `L`), a combination thereof (e.g. `gg` or even `ggg`), special keys (e.g. `<key_down>`, `key_up`) of modifiers in the following notation `<ctrl-j>`. See an example below:

```yaml
keymappings:
  ' ': mark_selected #spacebar
  /: search_mode
  <key_down>: scroll_down
  <key_up>: scroll_up
  '?': help
  G: jump_to_bottom
  e: edit
  gg: jump_to_top
  j: scroll_down
  k: scroll_up
  o: open
  q: quit
```
### Modifying Keyhints
Chained keymappings may be hard to remember. Papis-tui therefore displays hints in the bottom right corner, whenever the key you entered matches the start of (a) keychain(s) mapped to specific commands. However, if a command includes various and/or complex arguments, this becomes difficult to decipher (also, papis-tui may struggle to render it correctly if your arguments include special characters). You may therefore provide a short description of what the command is supposed to do, which will be displayed instead.

For instance, the `open` command accepts the `-d` flag to open a documents folder instead of the files attached. The `-r` argument can be used to filter available options based on the name of the files attached to a document (see `:open --help`). In order to access different options rapidly without having to remember this, you could configure the following keymappings.

```yaml
keymappings:
  'od':
    - open -d
    - "open directory"
  'op':
    - open -r 'pdf$'
    - "open pdf"
  'oh':
    - open -r 'html$'
    - "open html"
  'ot':
    - open -r 'txt$'
    - "open txt"
```

The first element in this list is the actual command being processed and the second one is the reader-friendly description. When hitting the `o`-key this should result in the keyhints displayed somewhat like this:

![image](https://github.com/supersambo/repo_pics/blob/main/modifying_keyhints.png?raw=true)

## statusbar
The statusbar can display context information on different aspects of your current session. Left and right side of the status bar can be customized using the same styling syntax as the multiline document display style. Context information is accessible via a dictionary named `info` with the following keys:

| key | description |
| --- | --- |
| `{info['idx']}` | Index of selected document among all documents in view |
| `{info['selected_win_idx']}` | Index of selected document on current window |
| `{info['marked']}` | Number of documents marked |
| `{info['items']}` | Number of documents in current library |
| `{info['view']}` | Number of documents in current view. That is result of search or filter |
| `{info['sortkeys']}` | Current keys used for sorting documents if any |
| `{info['mode']}` | Current mode, one of: `normal`, `command`, `select`, `search` |
| `{info['mode_upper']}` | Upper case mode |

The following is the default status bar included in the papis-tui minimal configuration:

```yaml
statusbar:
  left:
    default: "<black_white> {info["mode_upper"]} <black_white>"
  right:
    default: "<black_white> {info["idx"]} < {info["marked"]} < {info["view"]} < {info["items"]}  <black_white>"
```

Information content or style can also change depending on the mode you are currently in. For instance, if you wanted to change the color of the left side of statusbar when changing modes, you could do something like this:

```yaml
statusbar:
  left:
    default: "<black_white> {info["mode_upper"]} <black_white>"
    normal: "<black_white> {info["mode_upper"]} <black_white>"
    command: "<black_red> {info["mode_upper"]} <black_red>"
    search: "<black_magenta> {info["mode_upper"]} <black_magenta>"
```
In the above case papis-tui would fall back to the specified default mode, when in `select` mode, because no configuration for this mode is available.

## search keyword aliases
Search keyword aliases allow typing queries faster. Instead of typing `author: habermas` you might define an alias `a` for `author:`, `t` for `title:` etc.

```yaml
commandline:
  search:
    keyword_aliases: {a: 'author:', t: 'title:', y: 'year:', k: 'tags:'}
```

With this configuration in place the query `a habermas` gets automatically translated to `author: habermas` before being evaluated.

## info window
The info window is located below the documentlist and can be toggled on and of (set `default_on: True` to open it at startup). It is mainly intended for displaying the abstract of the selected document, but of course can be configured to be display something else. You can define as many different views as you want, each one requires a title and `content` field at least. Individual window heights can also be defined and as well as whether content should be linewrapped.

```yaml
infowindow:
  default_on: False
  views:
    abstract:
      content: "{doc['abstract']}"
      linewrap: True
      height: 8
    apa:
      content: "{format_reference(doc)}"
```

The `:info_toggle` command can be used to toggle the window on or off and views be changed with `:info_cycle`. You can scroll up the info_window up or down using `:info_scroll_up` and `:info_scroll_down`.

## Using papis-tui as the papis picker
In order to use papis-tui as the picker for papis you must specify this in your papis configuration file (not `papistui.yaml`!) under settings, which is usually located in `~/.config/papis/config`:

```ini
[settings]
picktool = papis-tui
```

# Special commands
## copy_to_clipboard
copy_to_clipboard is used to copy information about a selected document to the clipboard. How this information is formatted depends on the use case and can be fully customized. See some examples below:

```yaml
keymappings:
  yr:
    - copy_to_clipboard "(\\cite\{{doc['ref']}\})" #backslash and curly braces must be escaped
    - yank latex reference
  yu:
    - copy_to_clipboard "{doc['url']}"
    - yank url
  yt:
    - copy_to_clipboard "{doc['title']}"
    - yank title
```

## vim_send
vim_send is similar to copy_to_clipboard and can be configured the same way. Of course, the difference is that vim_send sends parsed string to a vim instance. This feature is highly experimental but should work with both vim and neovim in theory. In order to use this feature with vim you must start vim with the `--servername yourservername` option for it to be detectable. Neovim does not require any startup flags, but you must set the following option in your configuration file to use it:

```yaml
base:
  vimflavour: nvim #defaults to vim
```

When invoking the `vim_send` command for the first time it will connect to a server (if any is available) and send the evaluated string, or fail if none is available. If more than one is available, it will let you choose and remembers your selection. In case you want to change to another server later you can run `:vim_connect`.

## cmd
`cmd` provides the ability map shortcuts to commands which require mandatory positional arguments. Use cases for this could be `tag` and `sort` or `search`. You may want to hit the `t` key followed by a tag instead of typing `:tag` + *yourtag* in order to tag documents quickly. Similarly you may want to have a shortcut in place to search by *authorname* or *title* or sort your documents. This can be achieved with the following keymappings in place:

``` yaml
keymappings:
  t: cmd 'tag '
  S: cmd 'sort '
  sa: cmd -f 'author: '
  st: cmd -f 'title: '
```

## papis (calling papis from within papis-tui)
Most `papis` commands and command arguments are not implemented natively in `papis-tui`. Instead, the focus is to provide a useful and customizable user interface. However, `papis` can be called from within `papis-tui`, in the same manner one would do from the command line. This has the advantage that most features (including papis plugins) are available from within `papis-tui` and can be mapped to keys. In order to indicate which document a command should apply to, the following syntax can be used.

``` yaml
keymappings:
  e: papis edit papis_id:{doc['papis_id']} -e gedit
```

Here, `doc` resolves to the currently selected document and the `papis_id:...` syntax can be leveraged to call papis on one specific document. `docs` is also available as variable holding a list of all currently marked documents. Unfortunately, there doesn't seem to exist a syntax similar to `papis_id:...` that allows identify a set of documents yet.

# Roadmap
Some ideas I'd like to implement some day (in no particular order of relevance):

- [ ] Handle known bugs (see below)
- [X] Implement a general papis command
- [ ] ~~Implement papis `addto` command~~
- [ ] ~~Implement papis `merge` command~~
- [ ] ~~Implement papis `mv` command~~
- [ ] ~~Implement papis `update` command~~
- [ ] add options `--file` and `--notes` to `rm` command.
- [ ] allow unicode input on command line
- [ ] save per session command history (access via `<key_up>`) on command line
- [ ] Implement simple text completion on command line
- [ ] Improve code readability (including type-hints)
- [ ] Implement a plugin system

# Known bugs
- papis-tui fails the first time after the papis cache was cleared (`papis --cc`). This makes papis-tui practically unusable if you have papis configured not to use the cache at all `use-cache = False`.
- info window fails on some special characters (not sure which ones exactly), which causes papis-tui to crash completely

# See also
There are already quite a few document viewers/pickers, editor plugins for papis out there and there is even a built-in webapp:

- checkout the `papis serve` command (webapp)
- [papis-rofi](https://github.com/papis/papis-rofi/)
- [papis-dmenu](https://github.com/papis/papis-dmenu)
- [papis-vim](https://github.com/papis/papis-vim)
- [papis.nvim](https://github.com/jghauser/papis.nvim) (This one is amazing!)
- [papis-emacs](https://github.com/papis/papis.el)
