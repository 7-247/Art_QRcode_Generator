# Art_QRcode_Generator
同济大学 计算机科学导论 小组作业1

> http://http://49.235.64.119:5000/

## 项目动机
我们想做与图片处理相关的项目。我们观察到，微信名片二维码可以更改背景，比朴素的白底黑点好看。在网络上寻找好看的艺术二维码，发现网站中大部分素材都收费。于是，我们决定写一个自己的艺术二维码生成网站。并且，作为同济学生，我们精心设计了同济专属的艺术二维码，希望能让大家拥有属于同济人的独有的回忆。

## 语言
streamlit可以用非常少的代码完成一个好看而且功能实用的页面，但难以实现多网页、自定义元素位置等重要功能。因此最终我们转向了python flask。前端方面我们使用原生html+css+js，按照html5标准设计。

## 网页介绍
我们搭建的二维码生成网站允许大家上传任意的文本、链接、包括普通二维码，提交后生成艺术二维码并下载。

### 素材和美工
每位组员承担设计了一套或多套素材，最终完成了10套二维码。

首先，我们寻找用于代替原黑块的不同规格的素材。这里我们大量使用了iconfont矢量素材库，这里有大量的图标素材可供免费下载，且不用担心版权问题。

找到素材后，我们写了一个自动裁剪素材的黑白边框的python程序，并使用配色网站生成一套协调的配色，并据此重新使用photoshop修改素材。

当素材准备就绪后，我们按照一定的命名格式重命名，然后被另一个python程序读取，自动生成彩色二维码、灰度图、黑白二值化图，并分别判断是否可以被扫出，进一步调整素材。

### 前端
- 确定网页整体框架，最终做出来的成品的大致样子，用画图整了一个相当抽象的网页整体框架图。
- 将模板和css删改成我们需要的样式。
- 尝试加入动效。首先考虑了动态壁纸。通过面向f12调试，我们成功让动态壁纸显示在网页功能背后而不至错位。在这个过程中，我们熟悉了z-index和position的特性。然而，动态壁纸存在大量图片加载、显示长宽比无法兼容的问题。因此最终，我们使用js脚本实现动效。
- 细节优化：鼠标移到“提交文本”上会有额外提示；二维码切换时的淡入淡出效果；文字提醒会自动变化，以及“单击复制”的交互功能。

前端这玩意太玄学了。

### 后端
- 检测各种非法输入并制作error.html。上面展示错误信息，并延时自动返回首页。
- 通过时间戳管理不同二维码生成请求。
- 使用数据库管理，并编写了自适应的图片缓存清理。

### 算法
到底如何从普通黑白二维码生成彩色二维码？
- 假设我们制作一个简单的，素材只包含1×1和2×2规格的二维码。
- 首先我们通过bfs遍历来找到2×2的块并保存。
- 然后我们将这些2×2块用“福字”素材代替，将剩下的1×1块用左边四个素材来随机替换。
- 最后，给素材制作并添加合适的背景、自定义三个定位点的颜色，再给他取个名，一张艺术二维码就成功生成了。

### 服务
我们希望自己的网页从localhost:xxxx变成可以让大家直接访问的网页。

最终，我选择购买了一个云服务器，顺带再买了一个域名，并且成功将这个项目搭载上去。扫描右侧的二维码便可进入主页。

在服务器上搭建python，尤其是导入numpy库，可谓困难重重。因为服务器系统缺少各种framework框架和动态链接库dll文件。最后我直接进行了一个vs2019的安装，暴力解决了问题。

## 分工
    chy: 架构 设计 服务 性能优化 算法
    cs: 算法(二维码量化与替换)
    gzy: 前端
    pfr: 后端(数据管理)
    jrj: 前后端对接
    zkf: 测试
    yky: 美工
    全体成员参与素材设计


## References
> [python3 runoob](https://www.runoob.com/python3/python3-tutorial.html)<br>
> [python tutorial](https://www.runoob.com/manual/pythontutorial3/docs/html/introduction.html)<br>
> [streamlit 中文doc](http://cw.hubwiz.com/card/c/streamlit-manual/)<br>
> [图片生成配色网站](http://www.colorfavs.com/)<br>
