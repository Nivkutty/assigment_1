
from googleapiclient.discovery import build
import pymongo
import psycopg2
import pandas as pd
import streamlit as st



def Api_connect():
    Api_Id="AIzaSyDVrh_h_6oLW30TeZh4pdyYW8Uu2QbHbgE"
    api_service_name = "youtube"
    api_version = "v3"
    
    youtube = build(api_service_name,api_version,developerKey=Api_Id)
    return youtube
youtube = Api_connect()



    
def get_channel_info(channel_id):
            request = youtube.channels().list(part="snippet,ContentDetails,statistics",
                                              id = channel_id)

            response= request.execute()
            for i in response['items']:
                
                
                data = dict(Channel_Name=i['snippet']['title'],
                        Channel_Id=i['id'],
                        Subscriber=i['statistics']['subscriberCount'],
                        Views=i['statistics']['viewCount'],
                        Total_videos=i['statistics']['videoCount'],
                        Channel_description=i['snippet']['description'],
                       Playlist_id=i['contentDetails']['relatedPlaylists']['uploads'])
            return data
        


def get_videos_ids(channel_Id):
    video_ids=[]
    response=youtube.channels().list(id= channel_Id,
                                     part='contentDetails').execute()
    Playlist_id=response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    
    next_page_token= None
    
    while True:
        response1 = youtube.playlistItems().list(part='snippet',
                                                  playlistId=Playlist_id,
                                                  maxResults=50,
                                                 pageToken= next_page_token).execute()
        for i in range(len(response1['items'])):
            video_ids.append(response1['items'][i]['snippet']['resourceId']['videoId'])
        next_page_token = response1.get('nextPageToken')
        
        if next_page_token is None:
            break
    return video_ids



def get_video_info(video_Ids):
    
    
    
    video_data=[]
    for video_id in video_Ids:
            request=youtube.videos().list(part="snippet,ContentDetails,statistics",id=video_id)
            response= request.execute()

            for i in response['items']:
                
                data = dict(Channel_Name=i['snippet']['channelTitle'],
                        Channel_Id=i['snippet']['channelId'],
                        Video_Id=i['id'],
                        Title=i['snippet']['title'],
                        Tags=i['snippet'].get('tags'),
                        Thumbnail=i['snippet']['thumbnails']['default']['url'],
                        Description=i['snippet'].get('description'),
                        Published_Date=i['snippet']['publishedAt'],
                        Duration=i['contentDetails']['duration'],
                       Views=i['statistics'].get('viewCount'),
                        Likes=i['statistics'].get('likeCount'),  
                       Comments=i['statistics'].get('commentCount'),
                       Favourite_Count=i['statistics']['favoriteCount'],
                       Definition=i['contentDetails']['definition'],
                       Caption_Status=i['contentDetails']['caption'])
            video_data.append(data)
    return video_data




def get_comment_info(video_ids2):
    
    Comment_data=[]
    try:
        for video_id in video_ids2:


            request=youtube.commentThreads().list(part="snippet",videoId=video_id,maxResults=50)
            response= request.execute()

            for i in response['items']:
                
                data = dict(Comment_Id=i['snippet']['topLevelComment']['id'],
                            Video_Id=i['snippet']['topLevelComment']['snippet']['videoId'],
                            Comment_Text=i['snippet']['topLevelComment']['snippet']['textDisplay'],
                            Comment_Author=i['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                            Comment_Published=i['snippet']['topLevelComment']['snippet']['publishedAt'])
                
                Comment_data.append(data)
                
    except:
        pass


    return Comment_data



def get_playlist_details(channel_id):
    next_page_token= None
    All_data=[]
    while True:
        request=youtube.playlists().list(
                                         part='snippet,contentDetails',
                                         channelId=channel_id,
                                          maxResults=50,
                                          pageToken=next_page_token)
        response=request.execute()

        for i in response['items']:
                data = dict(Playlist_Id=i['id'],
                            Title=i['snippet']['title'],
                            Channel_Id=i['snippet']['channelId'],
                            Channel_Name=i['snippet']['channelTitle'],
                            PublishedAt=i['snippet']['publishedAt'],
                            Video_Count=i['contentDetails']['itemCount'])
                All_data.append(data)
        next_page_token=response.get('nextPageToken')     
        if next_page_token is None:
            break
    return All_data


client = pymongo.MongoClient("mongodb://localhost:27017")
db=client["youtube_data"]

def channel_details(channel_id):
    
    ch_details = get_channel_info(channel_id)
    pl_details = get_playlist_details(channel_id)
    vi_ids = get_videos_ids(channel_id)
    vi_details = get_video_info(vi_ids)
    com_details = get_comment_info(vi_ids)
    
    coll1=db["channel_details"]
    coll1.insert_one({"channel_information":ch_details,
                      "playlist_information":pl_details,"video_information":vi_details,"comment_information":com_details})
    return "upload completed succesfully"


def channels_table(channel_name_s):
    mydb= psycopg2.connect(host="localhost",
                          user="postgres",
                          password="Daimler",
                          database="youtube_data",
                          port="5432")
    cursor=mydb.cursor()
    
    create_query='''create table if not exists channels(Channel_Name varchar(100),
                                                             Channel_Id varchar(80) primary key,
                                                            Subscriber bigint,
                                                            Views bigint,
                                                           Total_videos int,
                                                           Channel_description text,
                                                           Playlist_Id varchar(80))'''
    
    
    cursor.execute(create_query)
    mydb.commit()

    

    single_channel_details=[]
    db=client["youtube_data"]
    coll1=db['channel_details']
    for ch_data in coll1.find({"channel_information.Channel_Name":channel_name_s},{"_id":0}):
        single_channel_details.append(ch_data["channel_information"])
    df_single_channel_details=pd.DataFrame(single_channel_details) 


    for index,row in df_single_channel_details.iterrows():
            insert_query='''insert into channels (Channel_Name,
                                                  Channel_Id,
                                                  Subscriber,
                                                  Views,
                                                  Total_videos,
                                                  Channel_description,
                                                  Playlist_id)

                                                  values(%s,%s,%s,%s,%s,%s,%s)'''
            values=(row['Channel_Name'],
                    row['Channel_Id'],
                    row['Subscriber'],
                   row['Views'],
                   row['Total_videos'],
                   row['Channel_description'],
                   row['Playlist_id'])
            try:
                cursor.execute(insert_query,values)
                mydb.commit()
            except:
                news=f"Your Provided Channel Name {channel_name_s} is Already exists"
                
                return news
                

            
                
                
def playlists_table(channel_name_s):

    mydb= psycopg2.connect(host="localhost",
                          user="postgres",
                          password="Daimler",
                          database="youtube_data",
                          port="5432")
    cursor=mydb.cursor()


    create_query='''create table if not exists playlists(Playlist_Id varchar(100) primary key,
                                                         Title varchar(100),
                                                        Channel_Id varchar(100) ,
                                                        Channel_Name varchar(100) ,
                                                       PublishedAt timestamp,
                                                       Video_Count int)'''
    
    cursor.execute(create_query)
    mydb.commit()
 
    
    single_playlists_details=[]
    db=client["youtube_data"]
    coll1=db['channel_details']
    for ch_data in coll1.find({"channel_information.Channel_Name":channel_name_s},{"_id":0}):
        single_playlists_details.append(ch_data["playlist_information"])
    df_single_playlists_details=pd.DataFrame(single_playlists_details[0]) 

  
    
    for index,row in df_single_playlists_details.iterrows():
            insert_query='''insert into playlists(Playlist_Id,
                                                  Title,
                                                  Channel_Id,
                                                  Channel_Name,
                                                  PublishedAt,
                                                  Video_Count)

                                                  values(%s,%s,%s,%s,%s,%s)'''
            values=(row['Playlist_Id'],
                    row['Title'],
                    row['Channel_Id'],
                   row['Channel_Name'],
                   row['PublishedAt'],
                   row['Video_Count'])
            
            cursor.execute(insert_query,values)
            mydb.commit()
            
def videos_table(channel_name_s):
    
    mydb= psycopg2.connect(host="localhost",
                  user="postgres",
                  password="Daimler",
                  database="youtube_data",
                  port="5432")
    cursor=mydb.cursor()




    create_query='''create table if not exists videos(Channel_Name varchar(100),
                    Channel_id varchar(100),
                    Video_Id varchar(30) primary key,
                    Title varchar(150),
                    Tags text,
                    Thumbnail varchar(200),
                    Description text,
                    Published_Date timestamp,
                    Duration interval,
                   Views bigint,
                    Likes bigint,  
                   Comments int,
                   Favourite_Count int,
                   Definition varchar(10),
                   Caption_Status varchar(50))'''
    
    


    cursor.execute(create_query)
    mydb.commit()


    single_videos_details=[]
    db=client["youtube_data"]
    coll1=db['channel_details']
    for ch_data in coll1.find({"channel_information.Channel_Name":channel_name_s},{"_id":0}):
        single_videos_details.append(ch_data["video_information"])
    df_single_videos_details=pd.DataFrame(single_videos_details[0])

    for index,row in df_single_videos_details.iterrows():
            insert_query='''insert into videos(Channel_Name,
                                                    Channel_Id,
                                                    Video_Id,
                                                    Title,
                                                    Tags,
                                                    Thumbnail,
                                                    Description,
                                                    Published_Date,
                                                    Duration,
                                                    Views,
                                                    Likes,  
                                                    Comments,
                                                    Favourite_Count,
                                                    Definition,
                                                    Caption_Status)

                                                    values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
            values=(row['Channel_Name'],
                    row['Channel_Id'],
                    row['Video_Id'],
                    row['Title'],
                    row['Tags'],
                    row['Thumbnail'],
                    row['Description'],
                    row['Published_Date'],
                    row['Duration'],
                    row['Views'],
                    row['Likes'],
                    row['Comments'],
                    row['Favourite_Count'],
                    row['Definition'],
                    row['Caption_Status'])

            cursor.execute(insert_query,values)
            mydb.commit()
            
def comments_table(channel_name_s):
    
    mydb= psycopg2.connect(host="localhost",
                      user="postgres",
                      password="Daimler",
                      database="youtube_data",
                      port="5432")
    cursor=mydb.cursor()

   


    create_query='''create table if not exists comments(Comment_Id varchar(100) primary key,
                                                        Video_Id varchar(50),
                                                        Comment_Text text,
                                                        Comment_Author varchar(150),
                                                        Comment_Published timestamp)'''
    


    cursor.execute(create_query)
    mydb.commit()

    single_comments_details=[]
    db=client["youtube_data"]
    coll1=db['channel_details']
    for ch_data in coll1.find({"channel_information.Channel_Name":channel_name_s},{"_id":0}):
        single_comments_details.append(ch_data["comment_information"])
    df_single_comments_details=pd.DataFrame(single_comments_details[0]) 

    for index,row in df_single_comments_details.iterrows():
                insert_query='''insert into comments(Comment_Id,
                                                        Video_Id,
                                                        Comment_Text,
                                                        Comment_Author,
                                                        Comment_Published)

                                                      values(%s,%s,%s,%s,%s)'''
                values=(row['Comment_Id'],
                        row['Video_Id'],
                        row['Comment_Text'],
                       row['Comment_Author'],
                       row['Comment_Published'])

                cursor.execute(insert_query,values)
                mydb.commit()
                
def tables(single_channel):
    
    news=channels_table(single_channel)
    if news:
        return news
    else:
        playlists_table(single_channel)
        videos_table(single_channel)
        comments_table(single_channel)
    
        return "Tables created Succesfully"



def show_channels_table():
    
    ch_list=[]
    db=client["youtube_data"]
    coll1=db['channel_details']
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        ch_list.append(ch_data['channel_information'])
    df = st.dataframe(ch_list)
    
    return df

def show_playlists_table():
    
    pl_list=[]
    db=client["youtube_data"]
    coll1=db['channel_details']
    for pl_data in coll1.find({},{"_id":0,"playlist_information":1}):
        for i in range (len(pl_data["playlist_information"])):
            pl_list.append(pl_data["playlist_information"][i])
    df1=st.dataframe(pl_list)
    
    return df1

def show_videos_table():
    
    vi_list=[]
    db=client["youtube_data"]
    coll1=db["channel_details"]
    for vi_data in coll1.find({},{"_id":0,"video_information":1}):
        for i in range(len(vi_data["video_information"])):
            vi_list.append(vi_data["video_information"][i])
    df2=st.dataframe(vi_list)
    
    return df2

def show_comments_table():
    
    com_list=[]
    db=client["youtube_data"]
    coll1=db["channel_details"]
    for com_data in coll1.find({},{"_id":0,"comment_information":1}):
        for i in range(len(com_data["comment_information"])):
            com_list.append(com_data["comment_information"][i])
    df3=st.dataframe(com_list)
    
    return df3

with st.sidebar:
    st.title(":red[YOUTUBE DATA HARVESTING AND WAREHOUSING]")
    st.header("Skill Take Away")
    st.caption("Python script")
    st.caption("Data Collection")
    st.caption("Mongo DB")
    st.caption("API Key")
    st.caption("Data Management using MongoDB and Sql")
channel_id = st.text_input("Enter the channel ID")

if st.button("collect and store data"):
    ch_ids=[]
    db= client["Youtube_data"]
    coll1= db["channel_details"]
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        ch_ids.append(ch_data["channel_information"]["Channel_Id"])
        
    if channel_id in ch_ids:
        st.success("Channels Details of the given channel id already exists")
        
    else:
        insert=channel_details(channel_id)
        st.success(insert)
        
all_channels=[]
db=client["youtube_data"]
coll1=db['channel_details']
for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
    all_channels.append(ch_data["channel_information"]["Channel_Name"])        
        
unique_channel= st.selectbox("Select the channel",all_channels) 

if st.button("Migrate to Sql"):
    Tables= tables(unique_channel)
    st.success(Tables)
    
show_table=st.radio("SELECT THE TABLE FOR VIEW",("Channels","Playlists","Videos","Comments"))

if show_table=="Channels":
    show_channels_table()
elif show_table=="Playlists":
    show_playlists_table()
elif show_table=="Videos":
    show_videos_table()
elif show_table=="Comments":
    show_comments_table()
    
mydb= psycopg2.connect(host="localhost",
                      user="postgres",
                      password="Daimler",
                      database="youtube_data",
                      port="5432")
cursor=mydb.cursor()

question= st.selectbox("Select Your Question",("1. All the videos and their corresponding channels names",
                                                "2. Channels have the most number of videos",
                                              "3. 10 most viewed videos and their respective channels",
                                              "4. Comments were made on each video",
                                              "5. Videos have the highest number of likes",
                                              "6. Total number of likes and dislikes for each video",
                                              "7. Total number of views for each channel",
                                              "8. Videos published in the year 2022",
                                              "9. Average duration of all videos in each channel",
                                              "10. Videos have the highest number of comments"))   

if question=="1. All the videos and their corresponding channels names":
    query1 = '''select title as videos,channel_name as channelname from videos '''
    cursor.execute(query1)
    mydb.commit()
    t1= cursor.fetchall()
    df= pd.DataFrame(t1,columns=["video title","channel name"])
    st.write(df)
    
elif question=="2. Channels have the most number of videos":
    query2 = '''select channel_name as channelname,total_videos as no_videos from channels order by total_videos desc  '''
    cursor.execute(query2)
    mydb.commit()
    t2= cursor.fetchall()
    df2= pd.DataFrame(t2,columns=["channel name","No of videos"])
    st.write(df2)    
    
elif question=="3. 10 most viewed videos and their respective channels":
    query3 = '''select views as views,channel_name as channelname,title as videotitle from videos 
                where views is not null order by views desc limit 10  '''
    cursor.execute(query3)
    mydb.commit()
    t3= cursor.fetchall()
    df3= pd.DataFrame(t3,columns=["views","channel name","video title"])
    st.write(df3)   
    
elif question=="4. Comments were made on each video":
    query4 = '''select comments as no_comments,title as videotitle from videos where comments is not null  '''
    cursor.execute(query4)
    mydb.commit()
    t4= cursor.fetchall()
    df4= pd.DataFrame(t4,columns=["no comments","video title"])
    st.write(df4)    
    
elif question=="5. Videos have the highest number of likes":
    query5 = '''select title as videotitle,channel_name as channelname,likes as likecount
                    from videos where likes is not null order by likes desc'''
    cursor.execute(query5)
    mydb.commit()
    t5= cursor.fetchall()
    df5= pd.DataFrame(t5,columns=["video title","channel name","likecount" ])
    st.write(df5)
    
elif question== "6. Total number of likes and dislikes for each video":
    query6 = '''select likes as likecount,title as videotitle from videos'''
    cursor.execute(query6)
    mydb.commit()
    t6= cursor.fetchall()
    df6= pd.DataFrame(t6,columns=["likecount","video title"])
    st.write(df6)
    
elif question==  "7. Total number of views for each channel":
    query7 = '''select channel_name as channelname,views as totalviews from channels'''
    cursor.execute(query7)
    mydb.commit()
    t7= cursor.fetchall()
    df7= pd.DataFrame(t7,columns=["channel name","totalviews"])
    st.write(df7)   
    
elif question== "8. Videos published in the year 2022":
    query8 = '''select title as videotitle,published_date as videorelease,
                channel_name as channelname from videos where extract (year from published_date)=2022'''
    cursor.execute(query8)
    mydb.commit()
    t8= cursor.fetchall()
    df8= pd.DataFrame(t8,columns=["video title","published_date","channel name"])
    st.write(df8)    
    
elif question== "9. Average duration of all videos in each channel":
    query9 = '''select channel_name as channelname,AVG(duration) as averageduration from videos group by channel_name'''
    cursor.execute(query9)
    mydb.commit()
    t9= cursor.fetchall()
    df9= pd.DataFrame(t9,columns=["channel name","averageduration"])


    T9=[]
    for index,row in df9.iterrows():
        channel_title=row["channel name"]
        average_duration=row["averageduration"]
        average_duration_str=str(average_duration)
        T9.append(dict(channeltitle=channel_title,avgduration=average_duration_str))
        df1=pd.DataFrame(T9)  
        st.write(df1)
    
elif question== "10. Videos have the highest number of comments":
    query10 = '''select title as videotitle,channel_name as channelname,comments as comments from videos 
                 where comments is not null order by comments desc '''
    cursor.execute(query10)
    mydb.commit()
    t10= cursor.fetchall()
    df10= pd.DataFrame(t10,columns=["video title","channel name","comments"])
    st.write(df10)    
    

    
    
                            








