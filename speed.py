from funtions import *
from multiprocessing import Pool, Manager
import os

# 初始化ssr节点占用端口，默认从60000开始
PORT = 60000

# 生成线程池
pool = Pool(50)
queue = Manager().Queue()

# 初始化节点相关文件存放目录
testFilesPath = os.path.join(config_dir, 'configJsonFiles')

cmd = '''
for i in `ps -ef | grep %s | awk '{print $2}'`
do
kill -9 ${i}
done
''' %(testFilesPath,)
os.system(cmd)

# 如果目录不存在就创建目录
if os.path.exists(testFilesPath):
    for file in os.listdir(testFilesPath):
        os.remove(os.path.join(testFilesPath, file))
else:
    os.mkdir(testFilesPath)


# 创建ssr信息列表
thread_list = list()

# 创建打印列表类
class DrawSpeedTable(object):
    '''工具类，打印表格格式化'''
    def __init__(self):
        self.table = []
        header = [
            "id",
            "name",
            "download(MB/s)",
            "upload(MB/s)",
            "server",
            "port",
            "method"
        ]
        self.x = PrettyTable(header)
        self.x.reversesort = True

    def append(self,*args,**kwargs):
        if(kwargs):
            content=[
                kwargs['id'],
                kwargs['name'],
                kwargs['download'],
                kwargs['upload'],
                kwargs['server'],
                kwargs['port'],
                kwargs['method'],
            ]
            self.x.add_row(content)

    def str(self):
        return str(self.x)

# 功能入口函数
def start_speed_test(pool):

    global PORT

    # 获取ssr字典列表
    if os.path.exists(SERVER_JSON_FILE_PATH):
        with open(SERVER_JSON_FILE_PATH, 'r') as file:
            json_str = file.read()
        ssr_info_dict_list = json.loads(json_str)
    else:
        ssr_info_dict_list = update_ssr_list_info()

    # 遍历ssr列表
    for ssr_info_dict in ssr_info_dict_list:
        if ssr_info_dict['port_status'] == '×':
            pass
        else:
            ssr_info_dict['local_address'] = LOCAL_ADDRESS
            ssr_info_dict['timeout'] = TIMEOUT
            ssr_info_dict['workers'] = WORKERS
            ssr_info_dict['local_port'] = PORT
            configJsonPath = os.path.join(testFilesPath,
                                          "{0}.json".format(ssr_info_dict_list.index(ssr_info_dict)))
            shadowcoskrPidFilePath = os.path.join(testFilesPath,
                                                  "{0}.pid".format(ssr_info_dict_list.index(ssr_info_dict)))

            shadowcoskrLogFilePath = os.path.join(testFilesPath,
                                                  "{0}.log".format(ssr_info_dict_list.index(ssr_info_dict)))

            startCmd = 'python3 {0} -c {1} -d start --pid-file {2} --log-file {3}'. \
                format(SHADOWSOCKSR_CLIENT_PATH,
                       configJsonPath,
                       shadowcoskrPidFilePath,
                       shadowcoskrLogFilePath)

            stopCmd = 'python3 {0} -c {1} -d stop --pid-file {2} --log-file {3}'. \
                format(SHADOWSOCKSR_CLIENT_PATH,
                       configJsonPath,
                       shadowcoskrPidFilePath,
                       shadowcoskrLogFilePath)

            ssr_info_dict['startCmd'] = startCmd
            ssr_info_dict['stopCmd'] = stopCmd
            ssr_info = json.dumps(ssr_info_dict, ensure_ascii=False, indent=4)

            with open(configJsonPath, 'w') as file:
                file.write(ssr_info)

            thread = pool.apply_async(ssr_speed_test, (PORT, ssr_info_dict))
            thread_list.append(thread)
            PORT = PORT + 1


if __name__ == "__main__":
    print("----start----")
    start_speed_test(pool)
    pool.close()
    pool.join()
    print("----end----")
    table = DrawSpeedTable()
    for thread in thread_list:
        ssr_info_dict = thread.get()
        table.append(
            id = 1,
            name = ssr_info_dict['remarks'],
            download = ssr_info_dict['download'],
            upload = ssr_info_dict['upload'],
            server = ssr_info_dict['server'],
            port = ssr_info_dict['server_port'],
            method = ssr_info_dict['method']
        )
    print(table.str())
