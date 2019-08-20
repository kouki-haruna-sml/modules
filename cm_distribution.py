import pandas as pd

'''
###############
引数df_cmは、rcのsimulated_cm_dfの[0]or[1]を取る
[0]を入れると

day_of_week: 曜日（日曜日が0、土曜日が6）
###############
'''

def cm_distribution(df_cm, channel_id, day_of_week):
    dic = {5:0, 6:0, 7:0, 8:0, 9:0, 10:0, 11:0, 12:0, 13:0, 14:0, 15:0, 16:0,\
               17:0, 18:0, 19:0, 20:0, 21:0, 22:0, 23:0, 0:0, 1:0, 2:0, 3:0, 4:0}

    for i in range(len(df_cm)):
        channel = df_cm["channel_id"][i]
        date = df_cm["started_at"][i]
        hour = date.hour
        dayofweek = date.dayofweek

        #5時開始用に曜日を調整
        if hour < 5:
            dayofweek -= 1

        if channel == channel_id:
            if dayofweek == day_of_week: #日曜日が0
                    dic[hour] += 1

    hours = 24
    for i in range(hours):
        if i not in list(dic.keys()):
            dic[i] = 0

    return list(dic.items())

def cm_distribution_df(df_cm):
    channel_id_ls = []
    weekday_ls = []
    hour_ls = []
    num_ls = []

    channels = [3, 4, 5, 6, 7]
    weekdays = 7
    hours = 24

    for i in channels:
        for j in range(weekdays):
            ls = cm_distribution(df_cm, i, j)

            for k in range(len(ls)):
                channel_id_ls.append(i)
                weekday_ls.append(j)
                hour_ls.append(ls[k][0])
                num_ls.append(ls[k][1])

    df = pd.DataFrame({"channel_id": channel_id_ls, "weekday": weekday_ls, "hour":hour_ls,  "num": num_ls})
    pivot_df = pd.pivot_table(df, index="hour", columns=["channel_id", "weekday"])
    df1 =  pivot_df.iloc[0:5]
    df2 =  pivot_df.iloc[5:24]
    result_df = pd.concat([df2, df1])

    return result_df

def cm_distribution_pivot_df(df_cm):
    channel_id_ls = []
    weekday_ls = []
    hour_ls = []
    num_ls = []

    channels = [3, 4, 5, 6, 7]
    weekdays = 7
    hours = 24

    for i in channels:
        for j in range(weekdays):
            ls = cm_distribution(df_cm, i, j)

            for k in range(len(ls)):
                channel_id_ls.append(i)
                weekday_ls.append(j)
                hour_ls.append(ls[k][0])
                num_ls.append(ls[k][1])

    df = pd.DataFrame({"channel_id": channel_id_ls, "weekday": weekday_ls, "hour":hour_ls,  "num": num_ls})
    pivot_df = pd.pivot_table(df, index="hour", columns=["channel_id", "weekday"])
    df1 =  pivot_df.iloc[0:5]
    df2 =  pivot_df.iloc[5:24]
    result_df = pd.concat([df2, df1])

    return result_df

#######change前は、queryのdf_cm
#######change後は、rc_ver2のsimulated_cm_df（返り値はタプルで、0がcm1のchange前、1がcm1のchange後）

def make_excel(file_name, df_cm):
    df = cm_distribution_df(df_cm)
    df.to_excel(file_name)

    wb = openpyxl.load_workbook(file_name)
    ws  = wb['Sheet1']

    #列幅の指定
    columns = ["B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", \
                      "V", "W", "X", "Y", "Z", "AA", "AB", "AC", "AD", "AE", "AF", "AG", "AH", "AI", "AJ"]
    for i in columns:
        ws.column_dimensions[i].width = 5


    #各セルの色ぬり　＆　0を空文字に
    for i in range(5, 29):
        for j in range(2, 40):
            value = ws.cell(row=i, column=j).value
            ws.cell(row=i, column=j).alignment = openpyxl.styles.Alignment(horizontal='center',vertical = 'center',wrap_text=True)
            if value == 0:
                ws.cell(row=i, column=j).value = ""
            elif value == 1:
                ws.cell(row=i, column=j).fill = openpyxl.styles.PatternFill(patternType="solid", fgColor='FFEEFF', bgColor='FFEEFF')
            elif value == 2:
                ws.cell(row=i, column=j).fill = openpyxl.styles.PatternFill(patternType="solid", fgColor='FFBBFF', bgColor='FFBBFF')
            elif value == 3:
                ws.cell(row=i, column=j).fill = openpyxl.styles.PatternFill(patternType="solid", fgColor='FF77FF', bgColor='FF77FF')
            elif value in (4, 5, 6, 7, 8, 9, 10):
                ws.cell(row=i, column=j).fill = openpyxl.styles.PatternFill(patternType="solid", fgColor='FF11FF', bgColor='FF11FF')
            else:
                pass

    wb.save(file_name)
