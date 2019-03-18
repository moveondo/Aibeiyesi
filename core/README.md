## 自动标注

###简介
研究员对招股书明书，年报公告等内容进行标注生成标签，如分红，重大风险，股权激励等
每个标注的段落对应一个相应的标题，记为标题对应标签 title --> label
研究员是对于一个段落标注，而对应关系是标题对标签，所以会有t1-->l1,t2-->l1,t3-->l2情况
据以上，是一个多分类问题，可训练出一个分类模型。本次首先多标注样本进行分类，所以可训练
出多个分类模型
任务:传入一个内容为一篇文章的各级标题以及所有的段落位置的json，预测出各段落对应的标签。

训练：
根据训练文件生成trainData.json，通过loadData_userTagging()解析该文件可得到
每个标题对应的标签，还有每个标签所属的bm_id等信息，之后根据bm_id分为多个模型

1.准备训练文件
从标注表里面查出研究员标注的文章的页码和offset和文章位置，存入到labelPosition.json
通过labelPosition.json找到标注对应的训练文件tree.json，之后就可构造训练集

训练参数：
trainDataFile = r'../data/trainData.json'  #训练集保存位置
labelPositionFile = r'../data/labelPosition.json' #用户标注信息保存为位置
以上两个参数默认，不可设置

设置bysparams.need_download = yes or no 决定是否要下载文章的tree.json，在本地执行时，使用yes 
设置bysparams.env = 'dev' 决定从生产数据库查出标注信息
bysparams.run_type = 'train' 使用训练模式
bysparams.change = 'no' 如果研究员有标注了新内容，需要再训练时，选择yes，可更新训练集
bysparams.model_path  = '../data/' 设置模型存储位置 
bysparams.new_trainData = 'no' 是否使用新的训练数据训练模型

设置好参数后，在集群上运行时，通过mq传入{"train_start":"yes"}，开始训练


预测：
*对json预处理,解析json后得到所有段落对应的标题
*依次将段落对应的标题送入模型预测出相应的分类标签
*根据段落中的startoffset和endoffset通过接口从后端获取正文
*过滤正文
*将符合条件的正文，以及对应的标签，id等相关信息插入数据库

设置bysparams.run_type = 'predict' 选择预测模式
设置bysparams.load_db_env = 'test' 将预测好的数据存入到测试数据库
设置bysparams.threshold = '-0.2' 阈值，过滤标题对应的分类
设置bysparams.predict_type = 'all' 全量预测，会先删除已预测好的数据
设置bysparams.predict_type = 'increment' 增量预测，保持原有预测数据，插入新的预测数据

设置好参数后，通过mq传入{"corp_anaylze_id":"12"}，会预测该公司研究下所有文章

