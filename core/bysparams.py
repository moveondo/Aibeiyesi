class BysParams():
    trainDataFile = r'../data/trainData.json'  #训练集保存位置
    labelPositionFile = r'../data/labelPosition.json' #用户标注信息保存为位置
    new_trainData = ''  #是否构建新的训练集
    model_path = ''      #模型存储位置
    filePath = ''     #预测文件文件夹
    env = ''             #运行环境，分为test和dev
    load_db_env = ''     #存储到数据库是环境，分为test和dev
    threshold = -0.2     #bys模型概率阀值
    run_type = ''            #运行模式，分为train训练模式和predict预测模式
    need_download = ''   #是否需要下载文件
    change = ''       #是否增加了新的标注
    user_id = ''       #user_id