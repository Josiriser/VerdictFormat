import json
import re
import requests
import cn2an
def Formal_to_Test(Formal_format_path,output_path):
    # 讀檔
    with open(Formal_format_path,'r',encoding='utf-8') as f:
        Formal_format=json.load(f)

    output_dict={}
    outputs_dict_list=[]
    for index,Formal_dict in enumerate(Formal_format):
        content_id=""
        name=Formal_dict["name"]
        job_location_list,job_title_list=get_job_location_and_title(Formal_dict["positions"])
        laws_list=get_laws_list(Formal_dict["laws"])

        output_dict["content_id"]=content_id
        output_dict["name"]=name
        output_dict["job_location"]=job_location_list
        output_dict["job_title"]=job_title_list
        output_dict["laws"]=laws_list
        outputs_dict_list.append(output_dict.copy())
        output_dict.clear()
    with open(output_path,"w",encoding="utf-8") as file:
        json.dump(outputs_dict_list,file,ensure_ascii=False)

def Test_to_Formal(Test_format_path,output_path):

    with open(Test_format_path,'r',encoding='utf-8') as f:
        Test_format=json.load(f)

    output_dict={}
    outputs_dict_list=[]
    for index,content_dict in enumerate(Test_format):
        # 先讀取測試格式資料
        content_id=content_dict["content_id"]
        name=content_dict["name"]
        job_location_list=content_dict["job_location"]
        job_title_list=content_dict["job_title"]
        laws_list=content_dict["laws"]        
        # 開始建立正式的格式
    
        # 先建立 positions 這個字典
        posistions_dict=get_posistions_dict(job_location_list,job_title_list)
        # print(posistions_dict)
        statuses_dict=get_statuses_dict()
        # print(statuses_dict)
        laws_dict=get_laws_dict(laws_list)
        # print(laws_dict)
        output_dict["name"]=name
        output_dict["statuses"]=statuses_dict
        output_dict["positions"]=posistions_dict
        output_dict["laws"]=laws_dict
        outputs_dict_list.append(output_dict.copy())
        output_dict.clear()

    with open(output_path,"w",encoding="utf-8") as file:
        json.dump(outputs_dict_list,file,ensure_ascii=False)

def Labeled_to_Test(Labeled_data):
    output_dict={}
    output_dict_list=[]
    for index,each_verdict in enumerate(Labeled_data):
        # 讀值
        doc_id=each_verdict["doc_id"]
        identities_list=extract_content_from_dict(json.loads(each_verdict["identities"]))
        laws_list=extract_content_from_dict(json.loads(each_verdict["laws"]))
        name=json.loads(each_verdict["name"])["content"]
        positions_list=extract_content_from_dict(json.loads(each_verdict["positions"]))
        units_list=extract_content_from_dict(json.loads(each_verdict["units"]))


        # 開始轉格式
        output_dict["content_id"]=doc_id
        output_dict["name"]=name
        output_dict["job_location"]=units_list
        output_dict["job_title"]=positions_list
        output_dict["laws"]=laws_list
        
        output_dict_list.append(output_dict.copy())
        output_dict.clear()
    return output_dict_list

def Multilaws_to_Normalize(CJ_text,Match_laws_list,Multilaws_dict_list,Break_line="\r\n"):
    Normalized_laws_list=[]
    for Multilaws_dict in Multilaws_dict_list:
        content=Multilaws_dict["content"]
        start=Multilaws_dict["start"]
        # 先找出法律名稱
        laws_name=get_laws_name(content,start,CJ_text,Match_laws_list,Break_line)
        # content 清洗
        # content=re.sub(Break_line,"",strip_blank(content))5
        # 判斷是否有法律名稱跟條是否包含在content
        regex_article="第\d*.*條"
        clean_content = re.sub(Break_line, "", strip_blank(content))
        laws_name_article_position = re.search(laws_name+regex_article, clean_content)
        # 若是沒有，往前找
        if laws_name_article_position==None:
            if re.search(regex_article, clean_content)== None:
                # 如果沒有第X條
                content=get_laws_name_and_article(content,start,CJ_text,laws_name+regex_article,Break_line)
            else:
                # 如果有第X條
                content = get_laws_name_and_article(
                    content, start, CJ_text, laws_name, Break_line)
        # 資料清洗
        clean_Multilaws=re.sub(Break_line,"",strip_blank(content))
        # 取出第幾條第幾項第幾款,act則用 laws_name代替
        act,article,paragraph,subparagraph=extract_laws_spa(clean_Multilaws)
        
        # 因為轉出來是數字，所以要再轉回字串
        s_article=""
        s_paragraph=""
        s_subparagraph=""
        if article!="":
            s_article="第"+str(article)+"條"
        if paragraph!="":
            s_paragraph="第"+str(paragraph)+"項"
        if subparagraph!="":
            s_subparagraph="第"+str(subparagraph)+"款"
        Normalized_laws_list.append(laws_name+s_article+s_paragraph+s_subparagraph)

    return Normalized_laws_list

def get_posistions_dict(job_location_list,job_title_list):

    posistions_dict={} 
    posistion_dict={}
    posistions_list=[] # 因為posistions 要放list
    # 可能什麼都沒有
    if len(job_location_list)==0 and len(job_title_list)==0:
        posistion_dict["work unit"]=""
        posistion_dict["title"]=""
        posistion_dict["locations"]=[]
        posistions_list.append(posistion_dict)
        posistions_dict["postitions"]=posistions_list.copy()  
    # 其中一個沒有
    elif len(job_location_list)==0 and len(job_title_list)!=0:
        for i in range(len(job_title_list)):
            posistion_dict["work unit"]=""
            posistion_dict["title"]=job_title_list[i]
            posistion_dict["locations"]=[]
            posistions_list.append(posistion_dict.copy())
            posistion_dict.clear()
        posistions_dict["postitions"]=posistions_list.copy()
    elif len(job_location_list)!=0 and len(job_title_list)==0:
        for i in range(len(job_location_list)):
            posistion_dict["work unit"]=job_location_list[i]
            posistion_dict["title"]=""
            posistion_dict["locations"]=[]
            posistions_list.append(posistion_dict.copy())
            posistion_dict.clear()
        posistions_dict["postitions"]=posistions_list.copy()
    # 可能會有多個職稱跟單位，全部配起來~
    else:
        for i in range(len(job_title_list)):
            for j in range(len(job_location_list)):
                posistion_dict["work unit"]=job_location_list[j]
                posistion_dict["title"]=job_title_list[i]
                posistion_dict["locations"]=[]
                posistions_list.append(posistion_dict.copy())
                posistion_dict.clear()
        posistions_dict["postitions"]=posistions_list.copy()

    return posistions_dict

def get_statuses_dict():
    statuses_dict={}
    status_dict={}
    statuses_list=[]
    status_dict["status"]=""
    status_dict["locations"]=[]
    statuses_list.append(status_dict)

    return statuses_list

def get_laws_dict(laws_list):
    # laws_dict裡面小的dict
    law_dict={}
    # 要回傳的dict
    laws_dict={}
    # 存放 law_dict 的list
    laws_dict_list=[]
    if len(laws_list)==0:
        laws_dict["laws"]=[] 
    else:
        for law in laws_list:
            act,article,paragraph,subparagraph=extract_laws_spa(law)
            law_dict["act"]=act
            if article!="":
                law_dict["article"]=article
            if paragraph!="":
                law_dict["paragraph"]=paragraph
            if subparagraph!="":
                law_dict["subparagraph"]=subparagraph
            law_dict["locations"]=[]
            laws_dict_list.append(law_dict.copy())
            law_dict.clear()
        laws_dict["laws"]=laws_dict_list
    return laws_dict

def extract_laws_spa(law):
    # 再百跟十之間補上一
    law=add_chinese_one(law)
    # 取出法條的款項條
    law=cn2an.transform(law, "cn2an")

    # 用阿拉伯數字寫數字
    regex_article="第\d*條"
    regex_paragraph="第\d*項"
    regex_subparagraph="第\d*款"


    # 假設都沒找到就回傳law
    act=law
    article=""
    paragraph=""
    subparagraph=""
    # 找第幾條，有找到再往下找第幾項
    article_position=re.search(regex_article,law)
    if article_position != None:
        # 取出act(法條名稱，不包含條項款)
        act=law[:article_position.start()]
        article_text=law[article_position.start():article_position.end()]
        # 取出數字
        article=get_laws_number(article_text)
        # 找第幾項，有找到再往下找第幾款
        paragraph_position=re.search(regex_paragraph,law)
        if paragraph_position != None:
            paragraph_text=law[paragraph_position.start():paragraph_position.end()]
            paragraph=get_laws_number(paragraph_text)
            subparagraph_position=re.search(regex_subparagraph,law)
            if subparagraph_position != None:
                subparagraph_text=law[subparagraph_position.start():subparagraph_position.end()]
                subparagraph=get_laws_number(subparagraph_text)

    return act,article,paragraph,subparagraph

def extract_laws_spa_json(law):
    act,article,paragraph,subparagraph=extract_laws_spa(law)
    law_dict={}
    law_dict["law"]=act
    if article=="":
        law_dict["article"]=-1
    else:
        law_dict["article"]=article
    if paragraph=="":
        law_dict["paragraph"]=-1
    else:
        law_dict["paragraph"]=paragraph
    if subparagraph=="":
            law_dict["subparagraph"]=-1
    else:
        law_dict["subparagraph"]=subparagraph
    
    return law_dict
def get_laws_number(laws_with_number):
    result=""
    for k in laws_with_number:
        if k.isdigit():
            result+=k
    if result!="":
        return int(result)
    else:
        return result

def get_job_location_and_title(Formal_dict_positions):
    job_location_list=[]
    job_title_list=[]
    for index,positions_dict in enumerate(Formal_dict_positions):
        job_location_list.append(positions_dict["work unit"])
        job_title_list.append(positions_dict["title"])
    return job_location_list,job_title_list

def get_laws_list(laws_dict):
    laws_list=[]
    
    for index,law_dict in enumerate(laws_dict):
        law=law_dict["act"]
        if "article" in law_dict:
            article=str(law_dict["article"])
            law = law+"第"+article+"條"
        if "paragraph" in law_dict:
            paragraph=str(law_dict["paragraph"])
            law = law +"第"+paragraph+"項"
        if "subparagraph" in law_dict:
            subparagraph=str(law_dict["subparagraph"])    
            law = law +"第"+subparagraph+"款"
        laws_list.append(law)
    return laws_list

def extract_content_from_dict(content_dict_list):
    content_list=[]
    for i in content_dict_list:
        content_list.append(strip_blank(i["content"]))
    return content_list

def strip_blank(dirty_str):
    # 去空白
    clean_str=re.sub(r"\s+","",dirty_str)
    return clean_str

def get_laws_name(laws,origin_start,CJ_text,Match_laws_list,Break_line):
    laws_name_dict_list=[]
    laws_name_dict={}
    # 先初始化
    laws_name_dict["law"]=""
    laws_name_dict["distance"]=99999999999
    for law in Match_laws_list:
        # 先找該法律名稱是否有在CJ_text
        if re.search(law,CJ_text)==None:
            continue
        else:
            # 如果所標記的法律已經含有 執掌法條  就直接return
            clean_laws=re.sub(Break_line,"",strip_blank(laws))
            if re.search(law,clean_laws) != None:
                return law
            # 找出所有位置
            all_match_positions=re.finditer(law,CJ_text)
            if len(laws_name_dict)==0:
                distance=99999999999
            else:
                distance=laws_name_dict["distance"]
            for match_position in all_match_positions:  
                # 計算距離多遠  並且法律名稱要在 origin_start 前面
                temp_distance= origin_start-match_position.start()
                # 要找跟laws最接近的位置
                if temp_distance < distance and temp_distance >=0 :
                    distance=temp_distance
                    laws_name_dict["law"]=law
                    laws_name_dict["distance"]=distance
    return laws_name_dict["law"]

def get_laws_name_and_article(laws,origin_start,CJ_text,laws_name_article_regx,Break_line):
    laws_name_dict_list=[]
    laws_name_dict={}
    # 先初始化
    laws_name_dict["law"]=""
    laws_name_dict["distance"]=99999999999
    # 找出所有位置
    all_match_positions=re.finditer(laws_name_article_regx,CJ_text)
    if len(laws_name_dict)==0:
        distance=99999999999
    else:
        distance=laws_name_dict["distance"]
    for match_position in all_match_positions:  
        # 計算距離多遠  並且法律名稱要在 origin_start 前面
        # print(match_position.group(),match_position.start())
        temp_distance= origin_start-match_position.start()
        # 要找跟laws最接近的位置
        if temp_distance < distance and temp_distance >=0 :
            distance=temp_distance
            laws_name_dict["law"]=match_position.group()+laws
            laws_name_dict["distance"]=distance
    return laws_name_dict["law"]

def add_chinese_one(law):
    new_law=""
    if re.search("百十",law)!=None:
        for token in law:
            if token=="百":
                new_law=new_law+token+"一"
            else:
                new_law=new_law+token
        return new_law
    else:
        return law

if __name__ == "__main__":
    file_path = "C:/Yao/工研院/Work/data/刑事判決_96,重訴,16_2008-03-06.json"
    # file_path = "C:/Yao/工研院/Work/data/law_test_marked.json"
    with open(file_path, 'r', encoding='utf-8') as f:
        full_text=json.load(f)
    CJ_text = full_text["full_doc"]
    Multilaws_dict_list=full_text["labeled_data"][0]["laws"]
    Match_laws_list=['中華民國刑法', '陸海空軍刑法', '國家機密保護法', '國家情報工作法', 
                    '國家安全法', '洗錢防制法', '臺灣地區與大陸地區人民關係條例', '貿易法', 
                    '組織犯罪防制條例', '人口販運防制法', '社會秩序維護法', '戰略性高科技貨品輸出入管理辦法', 
                    '山坡地保育利用條例', '公司法', '公民投票法', '公職人員選舉罷免法', 
                    '水土保持法', '水污染防治法', '水利法', '兒童及少年性交易防制條例', 
                    '空氣污染防制法', '金融控股公司法', '律師法', '政府採購法', '毒品危害防制條例',
                    '區域計畫法', '國有財產法', '票券金融管理法', '貪污治罪條例', 
                    '都市計畫法', '期貨交易法', '森林法', '稅捐稽徵法', '農田水利會組織通則',
                    '農會法', '農業金融法', '槍砲彈藥刀械管制條例', '漁會法', '銀行法',
                    '廢棄物清理法', '總統副總統選舉罷免法', '懲治走私條例', '藥事法', '證券交易法', 
                    '資恐防制法', '畜牧法', '破產法', '商標法', '商業登記法', '光碟管理條例',
                    '個人資料保護法', '健康食品管理法', '妨害國幣懲治條例', '通訊保障及監察法',
                    '化粧品衛生管理條例', '金融資產證券化條例', '食品安全衛生管理法',
                    '動物傳染病防治條例', '多層次傳銷管理法', '商業會計法', '信託業法',
                    '電信法', '動物用藥品管理法', '消費者債務清理條例', '專利師法',
                    '傳染病防治法', '嚴重特殊傳染性肺炎防治及紓困振興特別條例',
                    '農藥管理法', '飼料管理法', '管理外匯條例', '野生動物保育法',
                    '植物防疫檢疫法', '遺產及贈與稅法', '電子支付機構管理條例', 
                    '電子票證發行管理條例', '營業秘密法', '信用合作社法', '菸酒管理法', 
                    '保險法', '證券投資信託及顧問法', '證券投資人及期貨交易人保護法','刑法']
    
    Normalized_laws_list=Multilaws_to_Normalize(CJ_text,Match_laws_list,Multilaws_dict_list)
    print(Normalized_laws_list)
   
