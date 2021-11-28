# LightnovelSpider

本项目是一个基于 Python 3.9 开发的针对若干个轻小说相关网站的数据采集脚本集合，支持的网站和对应脚本文件如下表所示：

| 网站名称           | 首页地址                                                     | 脚本文件                           |
| ------------------ | ------------------------------------------------------------ | ---------------------------------- |
| 广州天闻角川       | [http://www.gztwkadokawa.com/](http://www.gztwkadokawa.com/) | kadokawa_cn.py                     |
| 台灣漫讀           | [https://www.bookwalker.com.tw/](https://www.bookwalker.com.tw/) | bookwalker_tw.py                   |
| 轻小说文库         | [https://www.wenku8.net/](https://www.wenku8.net/)           | wenku8_chapter.py, wenku8_image.py |
| 哩哔轻小说         | [https://www.linovelib.com/](https://www.linovelib.com/)     | libi_chapter.py, libi_image.py     |
| BOOK☆WALKER Japan  | [https://bookwalker.jp/](https://bookwalker.jp/)             | bookwalker_jp.py                   |
| BOOK☆WALKER Global | [https://global.bookwalker.jp/](https://global.bookwalker.jp/) | bookwalker_global.py               |

## 依赖的第三方库

请执行以下命令，安装其中未安装的第三方库：

```bash
pip3 install requests
pip3 install pyquery
pip3 install html2text
pip3 install markdown
```

## 开始前准备

### 创建SQLite3数据库文件

在项目根目录下创建名为`spider.db`的SQLite3数据库文件，在`spider.db`中执行SQL脚本`spider.sql`创建数据表。

### 创建图片文件夹

在项目根目录下创建文件夹，如下所示：

```bash
mkdir ./img
mkdir ./img/kadokawa_cn
mkdir ./img/bookwalker_tw
mkdir ./img/wenku8
mkdir ./img/libi
mkdir ./img/bookwalker_jp
mkdir ./img/bookwalker_global
```

### 准备Cookies

为使采集程序可以访问目标网站的所有内容，您应在相应网站注册账号，确保您已年满18岁，将登录后的cookies信息填入脚本的`cookie`变量中。有的脚本不需要`cookie`变量，则不填写。

### 设置代理服务器

在脚本的`proxy`变量中设置代理服务器地址。请确保代理服务器可以访问目标网站的所有内容。

### 可选设置

| 变量       | 含义                                                         |
| ---------- | ------------------------------------------------------------ |
| user_agent | 用户代理，用于伪装为普通网页浏览器                           |
| timeout    | 响应超时时间，单位为“秒”                                     |
| retry      | 请求发生错误时的重试次数，若超过此值，当前任务将被置于任务队列底部 |
| thread_num | 请求和数据处理使用的线程数目                                 |

## 注意事项

1. 执行`wenku8_image.py`和`libi_image.py`前必须先分别执行`wenku8_chapter.py`和`libi_chapter`。
2. 不建议修改`bookwalker_jp.py`和`bookwalker_global.py`的请求线程数，此二网站似乎有反爬虫机制，线程数超过5时有可能被临时封禁IP地址。
