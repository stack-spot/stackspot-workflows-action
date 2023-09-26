Markdown Guide

Markdown is a simple way to format text and looks clean on any device. By default, it does not have any specific formatting such as size, color, or font type.

The structures of your text are built by symbols, check the use of each one below.

Important notes:

1. It is possible to use HTML tags and their properties as a markup language, but its use is not recommended in documents as it pollutes the readability of Markdown.

2. To make it easier to edit your Markdown text, use a text editor like Visual Studio Code and Markdown preview plugins.
___

Italic text: *Italic* or _Italic_

Bold text: **Bold** or __bold__

Headers in Markdown have a total of 6 levels:

H1:
# Heading level 1

or

Heading 1
=========

H2:
## Heading level 2

or

Heading 2
---------

H3:
### Heading level 3

H4:
#### Heading level 4

H5:
##### Heading level 5

H6:
###### Heading level 6

Web Link: [Link Text](https://linkhere.com)

or

[Link Text Here][1]

[1]: https://linkaqui.com

Link to Images:

1- ![Image text](https://commonmark.org/help/images/favicon.png)
2- ![Image text](/path/folder/image.png)

Or

1- ![Image text][2]

[2]: https://commonmark.org/help/images/favicon.png

2- ![Image text][3]

[3]: /path/folder/image.png

Citation block:

> Quote block text

> Multiples
> Lines
> In the quote block

Unordered lists:

- item 1
- item 2
- item 3

Or

* item 1
* item 2
* item 3


Numbered lists:

1. Item 1
2. Item 2
3. Item 3

Or

1) Item 1
2) Item 2
3) Item 3

Horizontal line:

---

Or

***

Inline code:

inline `code snippet`.

Code blocks:

```
# code block
key: value
print some code
```