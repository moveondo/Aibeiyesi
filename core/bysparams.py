class BysParams():
    trainDataFile = r'../data/trainData.json'  #ѵ��������λ��
    labelPositionFile = r'../data/labelPosition.json' #�û���ע��Ϣ����Ϊλ��
    new_trainData = ''  #�Ƿ񹹽��µ�ѵ����
    model_path = ''      #ģ�ʹ洢λ��
    filePath = ''     #Ԥ���ļ��ļ���
    env = ''             #���л�������Ϊtest��dev
    load_db_env = ''     #�洢�����ݿ��ǻ�������Ϊtest��dev
    threshold = -0.2     #bysģ�͸��ʷ�ֵ
    run_type = ''            #����ģʽ����Ϊtrainѵ��ģʽ��predictԤ��ģʽ
    need_download = ''   #�Ƿ���Ҫ�����ļ�
    change = ''       #�Ƿ��������µı�ע
    user_id = ''       #user_id