import itertools
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from tqdm import tqdm

'''
#####################
リーチ率調査系
#####################
'''
def reach_rate(reached_panelers, valid_panelers):
    ls = list(reached_panelers.keys())
    count = 0
    for i in range(len(reached_panelers)):
        if ls[i] in valid_panelers:
            count += 1
    return count / len(valid_panelers)

def reach_over_n(reached_panelers, valid_panelers, n):
    keys_ls = list(reached_panelers.keys())
    values_ls = list(reached_panelers.values())
    count = 0

    for i in range(len(keys_ls)):
        if keys_ls[i] in valid_panelers and values_ls[i] >= n:
            count += 1
        else:
            pass
    return count

def reach_over_n_rate(reached_panelers, valid_panelers, n):
    keys_ls = list(reached_panelers.keys())
    values_ls = list(reached_panelers.values())
    count = 0
    for i in range(len(keys_ls)):
        if keys_ls[i] in valid_panelers and values_ls[i] >= n:
            count += 1
        else:
            pass
    return count / len(valid_panelers)



'''
#######################
CM枠交換による、リーチ変化シミュレーション系
#######################
'''

'''
#####################
振り分け

※query以外に使う引数
viewers =  list(cm1_viewers.values()) + list(cm2_viewers.values())

distributeされたCMの番号は、上のviewersの順番に従っている
#####################
'''

#振り分け用、部品
def score(valid_panelers, cm_viewers):
    #スコア
    score_ls = []
    for i in range(len(cm_viewers)):
        viewers = cm_viewers[i]
        count = 0
        for j in viewers:
            if j in valid_panelers:
                count += 1
        score = count / len(valid_panelers)
        score_ls.append(score)

    #偏差値化
    result = []
    mean = np.mean(score_ls)
    std = np.std(score_ls)
    for i in score_ls:
        deviation = (i - mean) / std
        deviation_value = round(50 + deviation * 10, 2)
        result.append(deviation_value)
    return np.array(result)

#振り分け用、部品
def make_df(cm1_valid_panelers, cm2_valid_panelers, viewers):
    cm1_score = score(cm1_valid_panelers, viewers)
    cm2_score = score(cm2_valid_panelers, viewers)
    t = np.array(cm1_score) - np.array(cm2_score)
    df = pd.DataFrame({"cm1_score": cm1_score, "cm2_score": cm2_score, "score": t})
    df = df.sort_values(by=["score"], ascending=False)
    return df

#振り分け用、部品
def pickup_no1(cm1_valid_panelers, cm2_valid_panelers, viewers):
    df = make_df(cm1_valid_panelers, cm2_valid_panelers, viewers)
    return df.index[0]

#振り分け用、部品
def update(cm1_valid_panelers, cm2_valid_panelers, viewers, cm_id):
    cm1_vp = cm1_valid_panelers.copy()
    cm2_vp = cm2_valid_panelers.copy()
    for i in viewers[cm_id]:
        if i in cm1_vp:
            cm1_vp.remove(i)
        if i in cm2_vp:
            cm2_vp.remove(i)
    return cm1_vp, cm2_vp

#CM枠をcm1、cm2にいい感じに振り分け
def distribute(cm1_valid_panelers, cm2_valid_panelers, cm1_viewers, cm2_viewers, df_cm1, df_cm2):
    #準備
    cm1_result = []
    cm2_result = []
    cm1_vp = cm1_valid_panelers.copy()
    cm2_vp = cm2_valid_panelers.copy()
    ls = sorted([len(df_cm1), len(df_cm2)])
    num1 = ls[0]
    num2 = ls[1]
    viewers = list(cm1_viewers.values()) + list(cm2_viewers.values())

    #CM数少ない方の個数分だけ振り分け
    for i in tqdm(range(num1)):
        df = make_df(cm1_vp, cm2_vp, viewers)
        #cm1
        for j in range(len(df)):
            no1_candidate = df.index[j]
            if (no1_candidate not in cm1_result) and (no1_candidate not in cm2_result):
                no1 = no1_candidate
                cm1_result.append(no1)
                cm1_vp = update(cm1_vp, cm2_vp, viewers, no1)[0]
                break

        #cm2
        for j in range(len(df)):
            no1_candidate = df.index[-(j+1)]
            if (no1_candidate not in cm2_result) and (no1_candidate not in cm1_result):
                no1 = no1_candidate
                cm2_result.append(no1)
                cm2_vp = update(cm1_vp, cm2_vp, viewers, no1)[1]
                break

    #残りの個数を振り分け
    if len(df_cm1) < len(df_cm2):
        for i in range(num2-num1):
            cm2_result.append(df.index[-(i+num1+1)])

    else:
        for i in range(num2-num1):
            cm1_result.append(df.index[-(i+num1+1)])

    return cm1_result, cm2_result

'''
########################
振り分けた結果
########################
'''
def simulation_result(cm1_valid_reach, cm2_valid_reach, \
                                      cm1_valid_panelers, cm2_valid_panelers, \
                                      cm1_viewers, cm2_viewers,\
                                      df_cm1, df_cm2):

    #cm振り分け
    cm1_num = len(df_cm1)
    tpl = distribute(cm1_valid_panelers, cm2_valid_panelers, cm1_viewers, cm2_viewers, df_cm1, df_cm2)
    cm1_distributed = tpl[0]
    cm2_distributed = tpl[1]

    print("distribution done")
    print("")
    print("-----------------------------------")

    #準備
    cm1_changed_viewers = []
    cm2_changed_viewers = []
    cm1_dic = {}
    cm2_dic = {}
    viewers = list(cm1_viewers.values()) + list(cm2_viewers.values())

    #cm1結果計算
    for i in cm1_distributed:
        for j in viewers[i]:
            cm1_changed_viewers.append(j)

    for i in cm1_changed_viewers:
        if i in cm1_valid_panelers:
            if i not in cm1_dic:
                cm1_dic[i] = 1
            else:
                cm1_dic[i] += 1

    #cm2結果計算
    for i in cm2_distributed:
        for j in viewers[i]:
            cm2_changed_viewers.append(j)

    for i in cm2_changed_viewers:
        if i in cm2_valid_panelers:
            if i not in cm2_dic:
                cm2_dic[i] = 1
            else:
                cm2_dic[i] += 1

    '''
    リーチ回数変えたいときは、以下を変えればok
    '''

    #cm1結果出力
    print("【CM1シミュレーション結果】")
    print("入れ替え前のリーチ人数：　", len(cm1_valid_reach))
    print("入れ替え前のリーチ率；　", len(cm1_valid_reach) / len(cm1_valid_panelers))
    print("")
    print("入れ替え後のリーチ人数: ", len(cm1_dic))
    print("入れ替え後のリーチ率： ", len(cm1_dic) / len(cm1_valid_panelers))
    print("")
    print("入れ替え前の対ターゲット総リーチ数；", sum(list(cm1_valid_reach.values())))
    print("入れ替え後の対ターゲット総リーチ数：", sum(list(cm1_dic.values())))
    print("")
    print("-----------------------------------")

    #cm2結果出力
    print("【CM2シミュレーション結果】")
    print("入れ替え前のリーチ人数：　", len(cm2_valid_reach))
    print("入れ替え前のリーチ率；　", len(cm2_valid_reach) / len(cm2_valid_panelers))
    print("")
    print("入れ替え後のリーチ人数: ", len(cm2_dic))
    print("入れ替え後のリーチ率： ", len(cm2_dic) / len(cm2_valid_panelers))
    print("")
    print("入れ替え前の対ターゲット総リーチ数；", sum(list(cm2_valid_reach.values())))
    print("入れ替え後の対ターゲット総リーチ数：", sum(list(cm2_dic.values())))

#cm_distribution接続用
def simulated_cm_df(cm1_valid_panelers, cm2_valid_panelers, cm1_viewers, cm2_viewers, df_cm1, df_cm2):
    #準備
    df = pd.concat([df_cm1, df_cm2])
    df1_started_at_ls = []
    df1_channel_id_ls = []
    df2_started_at_ls = []
    df2_channel_id_ls = []

    #cm振り分け
    tpl = distribute(cm1_valid_panelers, cm2_valid_panelers, cm1_viewers, cm2_viewers, df_cm1, df_cm2)
    cm1_distributed = tpl[0]
    cm2_distributed = tpl[1]

    #CM1分布
    for i in cm1_distributed:
        started_at = df.iloc[i]["started_at"]
        channel_id = df.iloc[i]["channel_id"]
        df1_started_at_ls.append(started_at)
        df1_channel_id_ls.append(channel_id)

    #CM2分布
    for i in cm2_distributed:
        started_at = df.iloc[i]["started_at"]
        channel_id = df.iloc[i]["channel_id"]
        df2_started_at_ls.append(started_at)
        df2_channel_id_ls.append(channel_id)

    #結果
    cm1_result_df = pd.DataFrame({"started_at": df1_started_at_ls, "channel_id": df1_channel_id_ls})
    cm2_result_df = pd.DataFrame({"started_at": df2_started_at_ls, "channel_id": df2_channel_id_ls})

    return cm1_result_df, cm2_result_df
