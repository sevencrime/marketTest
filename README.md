# 行情中心自动化测试框架

### 模块功能
* analysis        行情延时数据统计、分析、画图
>        -- collect_info 收集行情数据并入库，用于后续统计分析画图使用
>        -- do_analysis 对收集到的行情数据进行统计、分析、画图
* common        通用模块
>        -- test_log     日志模块  
>        -- tool     工具  
>            -- convert_pb_py3       pb转换工具  
>        -- basic_info       合约的基本信息  
>        -- common_method        基础的通用方法  
>        -- pb_method        pb的通用方法    
* pb_files        转换后的python pb文件
* py_redis        redis模块
>        -- base     基本方法
>        -- market       基于redis的行情相关的业务方法
* py_rocksdb        rocksdb模块
>        -- base     基本方法
>        -- market       基于rocksdb的行情相关的业务方法
* py_sqlite        sqlite模块
>        -- base     基本方法
>        -- market       基于sqlite的行情相关的业务方法
* report        存放report的地址，包括beautiful report, pytest report, allure report
* test_runner     运行整体测试用例的入口
* test_case       自动化测试用例
>        -- ws_testcase      websockets连接，订阅服务的用例
>            -- tool     订阅类相关的辅助工具
>                -- pc_subscribe_all_to_db       PC订阅所有行情数据并保存到sqlite
>                -- simple_app       简易交互式订阅App实现方法
>            -- *_testcase       测试用例
>        -- zmq_testcase     db 类的测试用例
>            -- zmq_record_test_case 测试入库后的zmq数据
>            -- cal_test_case    测试验证计算服务生成的rocksdb数据
* websocket_py3   websocket模块
>        -- ws_api   业务的api封装
>        -- ws_base  底层ws的封装，包括客户端、服务端
* zmq_py3     zmq模块
>        -- pub_sub      基于业务的zmq，pub\sub模式的收集数据
>        -- router_dealer      基于业务的zmq，router\dealer模式的收集数据
>        -- zmq_save_files       测试入库的sqlite数据
* run_market_app      启动简易交互式订阅App
* test_config     测试配置项
* test_instr_info     rocksdb测试合约列表

### 使用注意事项
1. 订阅类测试用例，可能存在调用zmq测试用例的情况，这样是为了校验数据的完整性和准确性
2. 请注意不要上传日志、缓存、数据库等数据
3. 当sqlite数据库达到千万级别的数据时，读取会慢一些，影响测试，建议清空再测试
4. rocksdb需要在linux环境运行，安装rocksdb环境，并加载对应数据库的磁盘镜像，
比如：sshfs eddid_dev@192.168.80.211:/data/workspace/dataStorage/bin/dbData/data /mnt/test_rocksdb -o allow_other
