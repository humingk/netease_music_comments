import sqlite3
import GetIP
import config
import ProxiesDataBase
import Util


def main():
    # 初始化数据库和数据表
    ProxiesDataBase.InitDB()
    # 刷新数据库，添加新数据
    Util.Refresh()
    # 获取一个代理使用
    proxies = Util.Get()
    print("=============================")
    print(str(proxies['http']))

    # 查询数据库多少条数据
    conn = sqlite3.connect(config.DBName)
    cu = conn.cursor()
    print(cu.execute("""SELECT * FROM {};""".format(config.TabelName)).fetchall().__len__())
    cu.close()
    conn.close()


if __name__ == '__main__':
    main()
