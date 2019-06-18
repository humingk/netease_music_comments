# !/usr/bin/env python
# -*- coding: utf-8 -*-

# author: humingk
# ----------------------
import json
import time

import pymysql

import config
from logger_tool import loggler_tool
from database_pool import database_pool
from netease.first_param import first_param
from netease.request_data import request_data
from thread_pool import thread_pool

logger = loggler_tool()


class song_comments:
    """
    歌曲评论获取类

    """

    def __init__(self):
        self.comments_list = []

    def get_song_comments_hot(self, song_id):
        """
        通过song_id获取热门评论

        :param song_id: 歌曲id
        """
        # 存歌曲信息
        pool = database_pool()
        pool.execute(
            "insert into song(song_id) values ({})".format(song_id)
        )
        pool.commit()
        # 获取热门评论
        content = self.get_song_page_comments(song_id=song_id, offset=0, limit=0)
        if content[0]:
            logger.debug("get_song_comments_hot success", "song_id:{}".format(song_id))
            return True, content[1]
        else:
            logger.error("get_song_comments_hot failed", "song_id:{}".format(song_id))
            return False, []

    def get_song_comments_normal(self, song_id, thread_count=config.song_comments_thread_count,
                                 song_comments_new_max=config.song_comments_new_max,
                                 song_comments_old_max=config.song_comments_old_max,
                                 limit=config.song_comments_page_limit):
        """
        通过song_id获取标准评论

        :param song_id: 歌曲id
        :param thread_count: 多线程个数
        :param song_comments_new_max: 最新评论最大数,详见config
        :param song_comments_old_max: 最旧评论最大数,详见config
        :param limit: 每一页获取标准评论数限制
        """
        # 获取标准评论总数
        content = self.get_song_page_comments(song_id=song_id, offset=0, limit=0, is_get_comment_total=True)
        try:
            if content[0]:
                comments_count = content[1]
                logger.info("get_song_comments_total_count success",
                            "song_id:{},total_count:{}".format(song_id, comments_count))
            else:
                return False, []
        except Exception as e:
            logger.error("get_song_comments_total_count failed", "song_id:{},error:{}".format(song_id, e))
            return False, []
        pool = database_pool()
        # 存歌曲信息
        pool.execute(
            "insert into song(song_id) values ({})".format(song_id)
        )
        pool.commit()

        # 多线程获取标准评论
        _thread_pool = thread_pool(20)
        for page in range(0,1000,100):
            _thread_pool.add(self.get_song_page_comments,
                             (song_id, config.song_comments_type_default, page, 100), None)
            time.sleep(5)

        return self.comments_list

    def get_song_page_comments(self, song_id, comment_type=config.song_comments_type_hot, offset=0, limit=0,
                               is_get_comment_total=False):
        """
        通过song_id获取某页评论

        :param song_id: 歌曲id
        :param comment_type: 评论类型,详见config
        :param offset: 位移量
        :param limit: 每页评论限制量
        :param is_get_comment_total: 是否为获取评论总数，默认否
        :return: 评论数据
        """
        # 请求参数
        _first_param = first_param().get_first_param_comment(offset=offset, limit=limit)
        # 请求数据
        content = request_data().get_request_data(first_param=_first_param[1], url=config.get_comments_url(song_id))
        try:
            if content[0]:
                if is_get_comment_total:
                    return True, json.loads(content[1])["total"]
                elif comment_type == config.song_comments_type_default:
                    json_data = json.loads(content[1])["comments"]
                elif comment_type == config.song_comments_type_hot:
                    json_data = json.loads(content[1])["hotComments"]
                else:
                    return False, []
            else:
                return False, []
        except Exception as e:
            logger.error("get_song_comments_page failed", "song_id:{},comment_type:{},offset:{},limit:{},error:{}"
                         .format(song_id, comment_type, offset, limit, e))
            return False, []
        pool = database_pool()
        comments_list = []
        for comment_json in json_data:
            comments_list.append(
                self.__add(comment_json=comment_json, pool=pool, comment_type=config.song_comments_type_hot))
        pool.commit()
        return True, comments_list

    def __add(self, comment_json, pool, comment_type=config.song_comments_type):
        """
        添加信息

        :param comment_json: 评论内容
        :param pool: 数据库线程池
        :param comment_type: 评论类型
        :return: 评论+用户信息
        """
        comment = {
            "comment_id": comment_json["commentId"],
            "comment_date": comment_json["time"],
            "comment_content": comment_json["content"],
            "comment_type": comment_type
        }
        user = {
            "user_id": comment_json["user"]["userId"],
            "user_name": comment_json["user"]["nickname"]
        }
        pool.execute(
            "insert into comment(comment_id, comment_date,comment_content,comment_type) values('{}',{},'{}',{})"
                .format(comment["comment_id"], comment["comment_date"],
                        pymysql.escape_string(comment["comment_content"]), comment["comment_type"]))
        pool.execute(
            "insert into user(user_id, user_name) values('{}','{}')"
                .format(user["user_id"], pymysql.escape_string(user["user_name"]))
        )
        pool.execute(
            "insert into user_comment(user_id, comment_id) values ('{}','{}')"
                .format(user["user_id"], comment["comment_id"])
        )
        pool.commit()
        return {"comment": comment}, {"user": user}


if __name__ == '__main__':
    # print(song_comments().get_song_page_comments(config.song_id, comment_type=config.song_comments_type_hot))
    # print(song_comments().get_song_comments_hot(config.song_id))
    print(song_comments().get_song_comments_normal(config.song_id, 5, 1000, 1000, 100))