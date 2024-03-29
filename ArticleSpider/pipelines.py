# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import json


from scrapy.pipelines.images import ImagesPipeline
from scrapy.exporters import JsonItemExporter
from twisted.enterprise import adbapi
import codecs
import MySQLdb
import MySQLdb.cursors


class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item


class JsonWithEncodingPipeline(object):
    # 自定义json文件的导出
    def __init__(self):
        self.file = codecs.open('article.json', 'w', encoding="utf-8")

    def process_item(self, item, spider):
        # ensure_ascii=False避免中文字符乱码
        lines = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(lines)
        return item

    def spider_closed(self, spider):
        self.file.close()


class JsonExporterPipeline(object):
    # 调用scrapy提供的json export导出json文件
    def __init__(self):
        self.file = open('articleexport.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding="utf-8", ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item


class MysqlPipeline(object):
    # 采用同步的机制写入mysql
    def __init__(self):
        # self.conn = MySQLdb.connect('host', 'user', 'passsword', 'dbname', charset="utf8", use_unicode=True)
        # self.conn = MySQLdb.connect('192.168.0.204', 'root', 'root', 'article_spider', charset="utf8", use_unicode=True)
        self.conn = MySQLdb.connect('47.98.154.117', 'work', 'Yeweiqqiang007!', 'article_spider', charset="utf8",
                                    use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = """
                   insert into cnblogs_article(title, create_date, url, author, url_object_id)
                   VALUES (%s, %s, %s, %s, %s)
               """
        self.cursor.execute(insert_sql,
                            (item["title"], item["create_date"], item["url"], item["author"], item["url_object_id"]))
        self.conn.commit()
        # 防止阻塞


class MysqlTwistedPipeline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        dbparms = dict(
            host=settings["MYSQL_HOST"],
            db=settings["MYSQL_DBNAME"],
            user=settings["MYSQL_USER"],
            passwd=settings["MYSQL_PASSWORD"],
            charset='utf8',
            cursorclass=MySQLdb.cursors.DictCursor,
            use_unicode=True,
        )
        dbpool = adbapi.ConnectionPool("MySQLdb", **dbparms)

        return cls(dbpool)

    def process_item(self, item, spider):
        # 使用twisted+mysql插入变成异步执行
        query = self.dbpool.runInteraction(self.do_insert, item)
        # query.addErrback(self.handle_error, item, spider)  # 处理异常

    def handle_error(self, failure, item, spider):
        # 处理异步插入的异常
        print(failure)

    def do_insert(self, cursor, item):
        # 执行具体的插入
        insert_sql = """
                          insert into cnblogs_article(title, create_date, url, author, url_object_id)
                          VALUES (%s, %s, %s, %s, %s)
                      """
        self.cursor.execute(insert_sql,
                            (item["title"], item["create_date"], item["url"], item["author"], item["url_object_id"]))


class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        pass
