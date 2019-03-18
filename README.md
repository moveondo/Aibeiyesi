##tf-dif+贝叶斯分类
###对文章标题进行分类，分类类别为用户标注
1.首先运行TrainData.py,构建出根据用户标注分类的训练数据集  

1.1 会生成../data/already_download.json文件，用来保存已经  
下载好的文件信息，每次运行时会检查该文件，避免重复下载

1.2 会生成../data/labelPosition.json文件，用来用户标注信息  
和对应的tree.json文件。每次运行时会检查该文件是否存在，避免  
重新读取用户标注记录数据库然后下载文件

1.3训练集存储在trainData.txt

