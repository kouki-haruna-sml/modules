#!/usr/bin/env python
#coding: utf-8

from sshtunnel import SSHTunnelForwarder
import psycopg2
import time
import pandas as pd
import numpy as np

'''
########################
オーロラ、レッドシフトそれぞれで
クエリを実行
########################
'''

def queryAurora(sql):
    with SSHTunnelForwarder(
      "prd-manage",
      ssh_pkey="/Users/haruna/.ssh/id_rsa",
      ssh_password="Sml11235813",
      remote_bind_address=("prod-smart-cluster.cluster-ro-copiyaqd3imr.ap-northeast-1.rds.amazonaws.com", 5432)
  ) as server:
        conn = psycopg2.connect(
              host="localhost",
              port=server.local_bind_port,
              dbname="smart",
              user="switch",
              password="THr8Tz7sTU4p")
        cur = conn.cursor()
        cur.execute(sql)
        result = cur.fetchall()

        colnames = [col.name for col in cur.description]
        new_result = [[one for one in one_result]  for one_result in result]
        result = pd.DataFrame(new_result,columns=colnames)

        cur.close()
        conn.close()
        time.sleep(0.1)
        return result

def queryRedShift(sql):
    with SSHTunnelForwarder(
      "prd-manage",
      ssh_pkey="/Users/haruna/.ssh/id_rsa",
      ssh_password="Sml11235813",
      remote_bind_address=("prod-smart.chbswrjeznvw.ap-northeast-1.redshift.amazonaws.com", 5439)
    ) as server:
        conn = psycopg2.connect(
              host="localhost",
              port=server.local_bind_port,
              dbname="smart",
              user="switch",
              password="THr8Tz7sTU4p")
        cur = conn.cursor()
        cur.execute(sql)
        result = cur.fetchall()

        colnames = [col.name for col in cur.description]
        new_result = [[one for one in one_result]  for one_result in result]
        result = pd.DataFrame(new_result,columns=colnames)

        cur.close()
        conn.close()
        time.sleep(0.1)
        return result

'''
#################################
lower_age 数値型
upper_age　数値型
gender      "'m'" or "'f'"
started_at  ex. "'2018-10-01'"
ended_at    ex. "'2018-10-31'"
period_num 期間数、数値型
region_id 数値型、関東→１、関西→２
#################################
'''
def valid_panelers(lower_age, upper_age, gender, started_at, ended_at, period_num, region_id):
    #少なくとも1期間有効なパネラー
    df = queryRedShift("select paneler_id \
                        from time_box_panelers\
                        where age >= {0} and age <= {1}\
                        and gender={2}\
                        and time_box_id in (\
                              select id  from time_boxes \
                              where started_at >= {3}\
                              and started_at <= {4}\
                              and region_id = {5})\
                    ;".format(lower_age, upper_age, gender, started_at, ended_at, region_id))

    #有効期間数の集計
    dic = {}
    for i in df["paneler_id"]:
        if i not in dic:
            dic[i] = 1
        else:
            dic[i] += 1

    #全期間有効パネラー
    valid_panelers_ls = []
    for i in dic.keys():
        if dic[i] == period_num:
            valid_panelers_ls.append(i)

    #出力
    return sorted(valid_panelers_ls)

'''
#####################################
product ex. "'%アクエリアズ%'"
started_at ex. "'2018-10-01'"
ended_at ex. "'2018-10-31'"
cm_type "spot" or "time"
region_id 数値型　関東→１、関西→２
gender 男→"'m'", 女"'f'"
lower_age 数値型
upper_age 数値型
#####################################
'''

def reached_panelers(product, started_at, ended_at, cm_type, region_id, gender, lower_age, upper_age):
    if cm_type == "spot":
        df = queryRedShift("with cm_id_with as (select cm_id from commercials \
                                                 where product_id in (select id from products where name like {0})\
                                                 and started_at >= {1}\
                                                 and started_at < {2}\
                                                 and not cm_type =2),\
                                 paneler_id_with as (select paneler_id \
                                                     from time_box_panelers\
                                                     where age >= {5} and age <= {6}\
                                                     and gender={4}\
                                                     and time_box_id in (select id from time_boxes \
                                                                          where started_at >= {1}\
                                                                          and started_at <= {2}\
                                                                          and region_id = {3}))\
                             select paneler_id from cm_viewers \
                             inner join commercials on cm_viewers.cm_id = commercials.cm_id and cm_viewers.started_at = commercials.started_at\
                             where cm_viewers.cm_id in (select cm_id from cm_id_with)\
                             and cm_viewers.started_at >= {1}\
                             and cm_viewers.started_at <= {2}\
                             and cm_viewers.region_id = {3}\
                             and cm_viewers.paneler_id in (select paneler_id from paneler_id_with)\
                             and not commercials.cm_type = 2\
                    ;".format(product, started_at, ended_at, region_id, gender, lower_age, upper_age))
    else:
        df = queryRedShift("with cm_id_with as (select cm_id from commercials \
                                                 where product_id in (select id from products where name like {0})\
                                                                      and started_at >= {1}\
                                                                      and started_at <= {2}\
                                                                      and cm_type =2),\
                                 paneler_id_with as (select paneler_id \
                                                     from time_box_panelers\
                                                     where age >= {5} and age <= {6}\
                                                     and gender={4}\
                                                     and time_box_id in (select id from time_boxes \
                                                                          where started_at >= {1}\
                                                                          and started_at <= {2}\
                                                                          and region_id = {3}))\
                             select paneler_id  from cm_viewers \
                             inner join commercials on cm_viewers.cm_id = commercials.cm_id and cm_viewers.started_at = commercials.started_at\
                             where cm_viewers.cm_id in (select cm_id from cm_id_with)\
                             and cm_viewers.started_at >= {1}\
                             and cm_viewers.started_at <= {2}\
                             and cm_viewers.region_id = {3}\
                             and cm_viewers.paneler_id in (select paneler_id from paneler_id_with)\
                             and commercials.cm_type = 2\
                    ;".format(product, started_at, ended_at, region_id, gender, lower_age, upper_age))

    dic = {}
    for i in df["paneler_id"]:
        if i not in dic:
            dic[i] = 1
        else:
            dic[i] += 1
    #dic_sorted = sorted(dic.items(), key=lambda x:x[0])

    return dic

'''
###################################
有効パネラーに含まれるリーチドパネラーを
絞り込む
###################################
'''
def valid_reach(reached_panelers, valid_panelers):
    valid_reach = {}
    for i in valid_panelers:
        if i in list(reached_panelers.keys()):
            valid_reach[i] = reached_panelers[i]
        else:
            pass
    return valid_reach

'''
####################################
product ex. "'%アクエリアス%'"
started_at ex. "'2018-10-01'"
ended_at ex. "'2018-11-01'"
cm_type "time" or "spot"
region_id 数値型　関東→1、関西→2
####################################
'''

def view_rate(product, started_at, ended_at, cm_type, region_id):
    if cm_type == "spot":
        df = queryRedShift("select cm_id, started_at, household_viewing_rate, channel_id from commercials \
                            where product_id in (\
                                    select id from products where name like {0})\
                                    and started_at >= {1}\
                                    and started_at <= {2}\
                                    and not cm_type = 2\
                                    and region_id = {3};".format(product, started_at, ended_at, region_id))
    else:
        df = queryRedShift("select cm_id, started_at, household_viewing_rate, channel_id from commercials \
                            where product_id in (\
                                    select id from products where name like {0})\
                                    and started_at >= {1}\
                                    and started_at <= {2}\
                                    and cm_type = 2\
                                    and region_id = {3};".format(product, started_at, ended_at, region_id))

    df = df.sort_values(by=["started_at"], ascending=True)
    return df

'''
############################
各種CM情報の取得
cm_infoは商品名から取得
cm_info2は番組名から取得
############################
'''
def cm_info(product, started_at, ended_at, cm_type, region_id):
    #視聴率や番組タイトル
    if cm_type == "spot":
        info_df = queryRedShift("select c.cm_id, c.prog_id, c.program_title, c.started_at, c.scene_id,\
                                  c.household_viewing_rate, c.channel_id, o.prog_type\
                                  from commercials c\
                                  inner join obi_programs o on c.prog_id = o.prog_id\
                                  where product_id in (select id from products where name like {0})\
                                  and started_at >= {1}\
                                  and started_at <= {2}\
                                  and not cm_type = 2\
                                  and region_id = {3};".format(product, started_at, ended_at, region_id))
    else:
        info_df = queryRedShift("select c.cm_id, c.prog_id,  c.program_title, c.started_at, c.scene_id,\
                                  c.household_viewing_rate, c.channel_id, o.prog_type\
                                  from commercials c\
                                  inner join obi_programs o on c.prog_id = o.prog_id\
                                  where product_id in (select id from products where name like {0})\
                                  and started_at >= {1}\
                                  and started_at <= {2}\
                                  and cm_type = 2\
                                  and region_id = {3};".format(product, started_at, ended_at, region_id))
    print("info done")

    #ビューアー
    if cm_type == "spot":
        viewers_df_interim = queryRedShift("with cm_with as (select cm_id, started_at from commercials\
                                                              where product_id in (select id from products\
                                                                                    where name like {0})\
                                                              and started_at >= {1}\
                                                              and started_at <= {2}\
                                                              and cm_type = 2)\
                                            select v.paneler_id, v.started_at \
                                            from cm_viewers v\
                                            inner join commercials c on v.cm_id = c.cm_id and v.started_at = c.started_at\
                                            where v.cm_id in (select cm_id from cm_with)\
                                            and v.started_at in (select started_at from cm_with)\
                                            and v.region_id = {3}\
                                            and not c.cm_type = 2\
                                            ;".format(product, started_at, ended_at, region_id))
    else:
        viewers_df_interim = queryRedShift("with cm_with as (select cm_id, started_at from commercials\
                                                              where product_id in (select id from products\
                                                                                    where name like {0})\
                                                              and started_at >= {1}\
                                                              and started_at <= {2}\
                                                              and cm_type = 2)\
                                            select v.paneler_id, v.started_at \
                                            from cm_viewers v\
                                            inner join commercials c on v.cm_id = c.cm_id and v.started_at = c.started_at\
                                            where v.cm_id in (select cm_id from cm_with)\
                                            and v.started_at in (select started_at from cm_with)\
                                            and v.region_id = {3}\
                                            and c.cm_type = 2\
                                            ;".format(product, started_at, ended_at, region_id))

    ls1 = viewers_df_interim.groupby("started_at")["paneler_id"].apply(list)
    ls2_interim = viewers_df_interim.groupby("started_at")["started_at"].apply(list)
    ls2 = []
    for i in range(len(ls2_interim)):
        ls2.append(ls2_interim[i][0])

    viewers_df = pd.DataFrame({"started_at": list(ls2), "paneler_id": list(ls1)})

    print("viewer done")

    #infoとviewersを結合
    result = pd.merge(info_df, viewers_df, on="started_at")

    result = result.sort_values(by=["started_at"], ascending=True)
    result = result.reset_index(drop=True)
    return result

'''
#################################
product ex. "'%アクエリアス%'"
started_at ex. "'2018-10-01'"
ended_at ex. "'2018-10-31'"
cm_type　"time" or "spot"
region_id 数値型　関東→１、関西→２
#################################
'''
def cm_viewers(product, started_at, ended_at, cm_type, region_id):
    if cm_type == "spot":
        df = queryRedShift("with cm_with as (select cm_id, started_at from commercials\
                                                                 where product_id in (select id from products\
                                                                                                       where name like {0})\
                                                                 and started_at >= {1}\
                                                                 and started_at <= {2}\
                                                                 and not cm_type = 2)\
                              select cm_viewers.paneler_id, cm_viewers.started_at from cm_viewers \
                              inner join commercials on cm_viewers.cm_id = commercials.cm_id and cm_viewers.started_at = commercials.started_at\
                              where cm_viewers.cm_id in (select cm_id from cm_with)\
                              and cm_viewers.started_at in (select started_at from cm_with)\
                              and cm_viewers.region_id = {3}\
                              and not commercials.cm_type = 2\
                              ;".format(product, started_at, ended_at, region_id))
    else:
        df = queryRedShift("with cm_with as (select cm_id, started_at from commercials\
                                                                 where product_id in (select id from products\
                                                                                                       where name like {0})\
                                                                 and started_at >= {1}\
                                                                 and started_at <= {2}\
                                                                 and cm_type = 2)\
                              select cm_viewers.paneler_id, cm_viewers.started_at from cm_viewers \
                              inner join commercials on cm_viewers.cm_id = commercials.cm_id and cm_viewers.started_at = commercials.started_at\
                              where cm_viewers.cm_id in (select cm_id from cm_with)\
                              and cm_viewers.started_at in (select started_at from cm_with)\
                              and cm_viewers.region_id = {3}\
                              and commercials.cm_type = 2\
                              ;".format(product, started_at, ended_at, region_id))

    ls1 = df.groupby("started_at")["paneler_id"].apply(list)
    ls2 = df.groupby("started_at")["started_at"].apply(list)

    dic = {}
    for i in range(len(ls1)):
        if ls2[i][0] not in dic:
            dic[ls2[i][0]] = ls1[i]
    return dic
