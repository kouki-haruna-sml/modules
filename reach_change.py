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
######################
（あるCMを抜いた時のリーチ3＋の減り）/ (そのCMを抜いた時のGRPの減り)
をスコアとして、低パフォーマンスのCMを見つけるための関数
######################
'''
def performance_score(cm_viewers, reached_panelers, valid_panelers, df_cm):
    rp = reached_panelers.copy()

    ########## R3+割合の変化 ##########
    cm_viewers_keys = list(cm_viewers.keys())
    count_ls = []

    #元々のリーチ3＋
    original_r3 = reach_over_n(reached_panelers, valid_panelers, 3)

    # i番目のCMを抜くと、リーチ3＋の人数は何人になるか
    #CM回数分繰り返し処理
    for i in range(len(cm_viewers)):
        reached_panelers = rp.copy()
        keys = list(cm_viewers.keys())[i]
        viewers = list(cm_viewers.values())[i]

        #CM各回の視聴者を一人ずつ
        count = 0
        for j in viewers:
            if j in list(reached_panelers.keys()):
                reached_panelers[j] -= 1

        #リーチ3＋の人数は何人になったか
        count = 0
        for k in list(reached_panelers.values()):
            if k >= 3:
                count += 1

        #リーチ3＋の減り
        diminish = original_r3 - count
        count_ls.append(diminish)

        # リーチ3+減り割合
        r3_rate_ls = []
        for i in range(len(count_ls)):
            r3_rate = count_ls[i] / len(valid_panelers)
            r3_rate_ls.append(r3_rate)

    ########## GRPの変化 ##########
    viewing_rate_ls = list(df_cm["household_viewing_rate"])

    ########## スコアの算出 ##########
    rate_ls = list(np.array(r3_rate_ls) / np.array(viewing_rate_ls))

    return rate_ls

def low_performance_cm(worst_num, performance_score_ls):
    dic = {}
    for i, j in enumerate(performance_score_ls):
        dic[i] = j
        dic_sorted = sorted(dic.items(), key=lambda x: x[1])
    return dic_sorted[:worst_num]


'''
######################
低パフォーマンスのものから全通りの組み合わせを生成し(combinations())、
その中から任意の個数をサンプリングする(sampling())
    ※exchange_target(=交換対象をworst何位までにするか)個の中から、exchange_num(=交換回数)個を交換
下2つの関数を使って、交換時のGRPの変化に制限をかける
######################
'''

def combinations(lp_cm_ls, exchange_num): #lp_cm_lsには、low_performanceの返り値を入れる
    ls = []
    for i in itertools.combinations(lp_cm_ls, r=exchange_num):
        ls.append(i)
    return ls

#exchange_target(=交換対象をworst何位までにするか)個の中から、exchange_num(=交換回数)個を交換
def sampling(exchange_target, exchange_num, cm1_score_ls, cm2_score_ls):
    cm1_lp_ls = low_performance_cm(exchange_target, cm1_score_ls)
    cm2_lp_ls = low_performance_cm(exchange_target, cm2_score_ls)

    cm1_target = combinations(list(cm1_lp_ls[i][0] for i in range(len(cm1_lp_ls))), exchange_num)
    cm2_target = combinations(list(cm2_lp_ls[i][0] for i in range(len(cm2_lp_ls))), exchange_num)

    cm1_target_sample = random.sample(cm1_target, 1) #1個ずつサンプルとる
    cm2_target_sample = random.sample(cm2_target, 1)

    return cm1_target_sample, cm2_target_sample

# sampled_lsにはsamplingの結果を入れる
def calc_GRP(sampled_ls, df_cm1, df_cm2):
    cm1_GRP = 0
    cm2_GRP = 0
    for i in range(len(sampled_ls[0])):
        for j in range(len(sampled_ls[0][0])):
            cm1_GRP += df_cm1["household_viewing_rate"].iloc[sampled_ls[0][i][j]]
    for i in range(len(sampled_ls[1])):
        for j in range(len(sampled_ls[1][0])):
            cm2_GRP += df_cm2["household_viewing_rate"].iloc[sampled_ls[1][i][j]]
    return abs(cm1_GRP - cm2_GRP)

def sampling_considering_GRP(max_GRP_change, exchange_target, exchange_num, cm1_score_ls, cm2_score_ls, df_cm1, df_cm2):
    count = 0
    while True:
        count += 1
        sampled_ls = sampling(exchange_target, exchange_num, cm1_score_ls, cm2_score_ls)
        score = calc_GRP(sampled_ls, df_cm1, df_cm2)
        if score < max_GRP_change:
            return sampled_ls
        else:
            #print(score)
            continue

'''
#######################
cm1_lp_ls, cm2_lp_ls →　低パフォーマンスCMのリスト(low_performance()を使う)
CMを入れ替えてリーチ3＋が何人に変化したかを返す関数
#######################
'''
def reach_over3_change(max_GRP_change, exchange_target, exchange_num,\
                        cm1_score_ls, cm2_score_ls,\
                        cm1_reached_panelers, cm2_reached_panelers,\
                        cm1_viewers, cm2_viewers,\
                        df_cm1, df_cm2):
    cm1_rp = cm1_reached_panelers.copy()
    cm2_rp = cm2_reached_panelers.copy()

    sample = sampling_considering_GRP(max_GRP_change, exchange_target, exchange_num, cm1_score_ls, cm2_score_ls, df_cm1, df_cm2)
    #①抜く処理
    #cm1
    for m in sample[0][0]:
        #抜くもの
        cm1_lp_viewers = list(cm1_viewers.values())[m]

        # low_performanceのCMを抜くと、リーチ3＋の人数は何人になるか
        for i in cm1_lp_viewers:
            if i in list(cm1_reached_panelers.keys()):
                cm1_rp[i] -= 1
            else:
                pass

    #cm2
    for m in sample[1][0]:
        #抜くもの
        cm2_lp_viewers = list(cm2_viewers.values())[m]

        # low_performanceのCMを抜くと、リーチ3＋の人数は何人になるか
        for i in cm2_lp_viewers:
            if i in list(cm2_reached_panelers.keys()):
                cm2_rp[i] -= 1
            else:
                pass

    #②足す処理
    ###cm1###
    for m in sample[1][0]:
        #足すもの
        cm2_lp_viewers = list(cm2_viewers.values())[m]

        # low_performanceのCMを足すと、リーチ3＋の人数は何人になるか
        for j in cm2_lp_viewers:
            if j in list(cm1_reached_panelers.keys()):
                cm1_rp[j] += 1
            else:
                pass

    ###cm2###
    for m in sample[0][0]:
        cm1_lp_viewers = list(cm1_viewers.values())[m]
        for j in cm1_lp_viewers:
            if j in list(cm2_reached_panelers.keys()):
                cm2_rp[j] += 1
            else:
                pass

    #③リーチ3＋の人数は何人になったか
    cm1_count = 0
    for k in list(cm1_rp.values()):
        if k >= 3:
            cm1_count += 1
        else:
            pass

    cm2_count = 0
    for k in list(cm2_rp.values()):
        if k >= 3:
            cm2_count += 1
        else:
            pass

    return cm1_count, cm2_count

'''
########################
シミュレーション結果
########################
'''
#R3+何人になったか
def simulation_result(max_GRP_change, sample_num, exchange_target, exchange_num, cm1_score_ls, cm2_score_ls,cm1_reached_panelers, cm2_reached_panelers,cm1_viewers, cm2_viewers, df_cm1, df_cm2):
    result = []
    for _ in range(sample_num):
        t = reach_over3_change(max_GRP_change, exchange_target, exchange_num,cm1_score_ls, cm2_score_ls,cm1_reached_panelers, cm2_reached_panelers,cm1_viewers, cm2_viewers, df_cm1, df_cm2)
        result.append(t)
    return result

#R3+人数の増減
def simulation_result_r3change(max_GRP_change, sample_num, exchange_target, exchange_num,\
                                cm1_original_r3, cm2_original_r3,\
                                cm1_score_ls, cm2_score_ls,\
                                cm1_reached_panelers, cm2_reached_panelers,\
                                cm1_valid_panelers, cm2_valid_panelers, \
                                cm1_viewers, cm2_viewers, df_cm1, df_cm2):

    simulated_result = simulation_result(max_GRP_change, sample_num, exchange_target, exchange_num, \
                                        cm1_score_ls, cm2_score_ls,\
                                        cm1_reached_panelers, cm2_reached_panelers,\
                                        cm1_viewers, cm2_viewers, df_cm1, df_cm2)

    result = []
    for i in tqdm(range(len(simulated_result))):
        cm1_r3_change = simulated_result[i][0] - cm1_original_r3
        cm2_r3_change = simulated_result[i][1] - cm2_original_r3
        result.append([cm1_r3_change, cm2_r3_change])

    return result

#R3+人数増減の期待値
def simulation_result_expected_value(max_GRP_change, sample_num, exchange_target, exchange_num,\
                                                                    cm1_original_r3, cm2_original_r3,\
                                                                    cm1_score_ls, cm2_score_ls,\
                                                                    cm1_reached_panelers, cm2_reached_panelers,\
                                                                    cm1_valid_panelers, cm2_valid_panelers, \
                                                                    cm1_viewers, cm2_viewers,\
                                                                    df_cm1, df_cm2):
    simulated_result = simulation_result(max_GRP_change, sample_num, exchange_target, exchange_num, \
                                        cm1_score_ls, cm2_score_ls,\
                                        cm1_reached_panelers, cm2_reached_panelers,\
                                        cm1_viewers, cm2_viewers, df_cm1, df_cm2)

    cm1_r3_change_dic = {}
    cm2_r3_change_dic = {}
    for i in range(len(simulated_result)):
        cm1_r3_change = simulated_result[i][0] - cm1_original_r3
        cm2_r3_change = simulated_result[i][1] - cm2_original_r3

        if cm1_r3_change not in cm1_r3_change_dic:
            cm1_r3_change_dic[cm1_r3_change] = 1
        else:
            cm1_r3_change_dic[cm1_r3_change] += 1

        if cm2_r3_change not in cm2_r3_change_dic:
            cm2_r3_change_dic[cm2_r3_change] = 1
        else:
            cm2_r3_change_dic[cm2_r3_change] += 1

    cm1_r3_probability = {}
    cm2_r3_probability = {}
    cm1_expected_value = 0
    cm2_expected_value = 0

    for i, j in zip(list(cm1_r3_change_dic.keys()), list(cm1_r3_change_dic.values())):
        probability = j / len(simulated_result)
        cm1_r3_probability[i] = probability
        t = i * probability
        cm1_expected_value += t

    for i, j in zip(list(cm2_r3_change_dic.keys()), list(cm2_r3_change_dic.values())):
        probability = j / len(simulated_result)
        cm2_r3_probability[i] = probability
        t = i * probability
        cm2_expected_value += t

    print("cm1 確率分布", cm1_r3_probability)
    print("cm2 確率分布", cm2_r3_probability)
    print("cm1 期待値：", cm1_expected_value)
    print("cm2 期待値", cm2_expected_value)
    return cm1_expected_value, cm2_expected_value

'''
########################
シミュレーション結果可視化
########################
'''

def plot_visualize(cm1_name, cm2_name, \
                    max_GRP_change, sample_num, exchange_target, exchange_num, \
                    cm1_original_r3, cm2_original_r3, \
                    xlim, ylim, \
                    cm1_score_ls, cm2_score_ls, \
                    cm1_reached_panelers, cm2_reached_panelers,\
                    cm1_valid_panelers, cm2_valid_panelers, \
                    cm1_viewers, cm2_viewers, \
                    df_cm1, df_cm2):

    plt.figure(facecolor="w", figsize=(12, 12))
    plt.subplots_adjust(wspace=0.6, hspace=0.6)

    for i in tqdm(range(9)):
        ls = simulation_result_r3change(max_GRP_change, sample_num, exchange_target, i,\
                                                                cm1_original_r3, cm2_original_r3,\
                                                                cm1_score_ls, cm2_score_ls,\
                                                                cm1_reached_panelers, cm2_reached_panelers,\
                                                                cm1_valid_panelers, cm2_valid_panelers, \
                                                                cm1_viewers, cm2_viewers, df_cm1, df_cm2)

        x = [ls[i][0] for i in range(len(ls))]
        y = [ls[i][1] for i in range(len(ls))]

        fill_x = np.linspace(0,  xlim, 20)

        plt.subplot(3, 3, i+1)
        plt.fill_between(fill_x, 0, ylim, facecolor="lightgray")
        plt.grid(True)
        plt.title("Exchange Num: {}".format(i+1))
        plt.xlabel(cm1_name)
        plt.ylabel(cm2_name)

        plt.plot(np.linspace(-xlim, xlim, 20), [0]*20, c="orange")
        plt.plot([0]*20, np.linspace(-ylim, ylim, 20), c="orange")
        plt.scatter(x, y)

'''
#CM片方のリーチ3+変化をグラフに
def visualize(generated_ls, exchange_target):
    fig = plt.figure(facecolor="w", figsize=(10, 6))
    plt.grid(True)
    ax = plt.subplot()
    ax.set_ylim(190, 225) #################変える
    ax.set_xlim(0.5, exchange_target)
    plt.xlabel("Exchange")
    plt.ylabel("Reach 3+")
    plt.xticks(range(exchange_target))
    plt.title("Exchange Target : {}".format(exchange_target))

    #元々のリーチ3＋の人数
    plt.plot(np.linspace(0, exchange_target+1, exchange_target+1), [205]*(exchange_target+1), label="before exchange") ##########205変える

    #入れ替え後のリーチ3+
    for i, j in enumerate(generated_ls):
        plt.scatter([i+2]*50, j) #############50　サンプル数に合わせて変える

    #入れ替え後のリーチ3+の人数の平均
    plt.plot(np.linspace(2, exchange_target - 5, exchange_target-6), mean(generated_ls), label="after exchange")   ###########5,6 変える




    print(mean(generated_ls))

    plt.legend()

def graph_visualize(sample_num, exchange_target, exchange_num, \
                                   cm1_score_ls, cm2_score_ls, \
                                   cm1_reached_panelers, cm2_reached_panelers, \
                                   cm1_viewers, cm2_viewers, \
                                   df_cm1, df_cm2):
    result_ls = []
    for i in range(exchange_target-10):
        result = simulation_result(sample_num, exchange_target, i+1, \
                                                                            cm1_score_ls, cm2_score_ls, \
                                                                            cm1_reached_panelers, cm2_reached_panelers, \
                                                                            cm1_viewers, cm2_viewers, \
                                                                             df_cm1, df_cm2)
        result_ls.append(simulation_result)
    return result_ls
'''
