import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
from src import sql
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from openai import OpenAI

# Plot configurations
FIG_W = 10 # Width of plots
FIG_H = 5 # Height of plots
ROT = 0 # Rotation of x-axis labels
TS = 15 # Title size

def barplot_channel_video_count(df_all, channel_ids):
    '''Create a barplot and save the image to a folder. Return image name. Take a dataframe with videodata  as input. Input channel_ids to render image name.'''

    channel_ids_string = '_'.join(channel_ids)
    image_name = f'static/images/{channel_ids_string}_barplot_channel_video_count.png'

    plt.figure(figsize=(FIG_W, FIG_H))
    # Agrupar los videos por canal y contar la cantidad de videos
    df_all.groupby('channel_title').size().sort_values(ascending=False).plot.bar()
    plt.xticks(rotation=ROT)
    plt.xlabel("Nombre del Canal")
    plt.ylabel("Cantidad de Videos")
    plt.title('Cantidad de videos por canal', fontdict = {'fontsize' : TS})
    plt.savefig(image_name, dpi=100)

    return image_name

def histogram_video_duration_count(df_all, channel_ids):
    '''Create a histogram and save the image to a folder. Return image name. Take a dataframe with videodata  as input. Input channel_ids to render image name.'''

    df_all['duration_min'] = df_all['duration_sec'].astype('int') / 60

    # Calcular el outlier (datos atipicos) y limpiar los datos
    outlier = (df_all['duration_min'].describe()['75%'] - df_all['duration_min'].describe()['25%']) * 1.5 + df_all['duration_min'].describe()['75%']
    df_all = df_all[df_all['duration_min'] <= outlier]

    bin_size = int(df_all['duration_min'].max())
    labels = df_all['channel_title'].unique()

    data = []
    for channel in labels:
        video_durations = df_all[df_all['channel_title'] == channel]['duration_min'].to_numpy()
        data.append(video_durations)

    # Crear nombre de img
    channel_ids_string = '_'.join(channel_ids)
    image_name = f'static/images/{channel_ids_string}_histogram_video_duration_count.png'

    plt.figure(figsize=(FIG_W, FIG_H))
    plt.hist(data, bins=bin_size, alpha=0.5)
    plt.legend(labels) 
    plt.xlabel('Duración de los videos en minutos')
    plt.ylabel('Cantidad de videos')
    plt.title('Recuento de vídeos y duraciones', fontdict = {'fontsize' : TS})

    plt.savefig(image_name, dpi=100)

    return image_name

def histogram_video_duration_count_single(df_all, channel_id, channel_title=None):
    '''Create a histogram and save the image to a folder. Return image name. Take a dataframe with videodata  as input. Input channel_ids to render image name.'''

    df_all = df_all[df_all['channel_id'] == channel_id]

    # Calculate outlier and clean them
    outlier = (df_all['duration_sec'].describe()['75%'] - df_all['duration_sec'].describe()['25%']) * 1.5 + df_all['duration_sec'].describe()['75%']
    df_all = df_all[df_all['duration_sec'] <= outlier]

    df_all['duration_min'] = df_all['duration_sec'] / 60
    df_all['duration_min'] = df_all['duration_min'].astype('int32')

    bin_size = df_all['duration_min'].max()
    if bin_size < 1:
        bin_size = 1

    image_name = f'static/images/{channel_id}_histogram_video_duration_count.png'

    plt.figure(figsize=(FIG_W, FIG_H))
    plt.hist(df_all['duration_min'], bins=bin_size, alpha=0.5, edgecolor='black', linewidth=1)
    plt.legend(df_all['channel_title'].unique())
    plt.title(f'Contador duracion por video para "{channel_title}"', fontdict = {'fontsize' : TS})
    plt.xlabel('Duracion del video en minutos')
    plt.ylabel('Contador de videos')
    plt.xlim(0,bin_size)
    plt.savefig(image_name, dpi=100)

    return image_name

def barplot_links(video_df, channel_ids):
    '''Create a barplot with counts on how many video descriptions hae clickable links. Save the plot as image.'''

    # Check if there is 'http' in description and insert result
    video_df['Links in decription'] = video_df['description'].str.contains('http').apply(lambda x: 'Links Clickables' if x else 'Links No Clickables')

    channel_ids_string = '_'.join(channel_ids)
    image_name = f'static/images/{channel_ids_string}_barplot_links.png'

    video_df = video_df.groupby(['channel_title', 'Links in decription'])[['video_id']].count().reset_index()
    sns.set(style="whitegrid")
    g = sns.catplot(x="channel_title",
                    y="video_id",
                    hue="Links in decription",
                    data=video_df,
                    height=6,
                    kind="bar",
                    palette="muted"
    )
    g.despine(left=True)
    g.set_xlabels("Nombre del Canal")
    g.set_ylabels("Contador de videos")
    # g.set_title('Links in Video Descriptions', fontdict = {'fontsize' : TS})
    plt.savefig(image_name, dpi=100)

    return image_name

def create_wordcloud(text, stopwords=STOPWORDS,video_id=None, channel_title=None):
    '''Return a word cloud image name and save the image. Take as input a string of text and a video id or a channel name for creating the title.'''

    wordcloud = WordCloud(
        max_font_size=50,
        min_font_size=10,
        max_words=100,
        prefer_horizontal=1,
        # for transparnt background: mode='RGBA', background_color=None
        # mode="RGBA",
        background_color="white",
        stopwords=stopwords,
        # Increase for lager images
        scale=2.0,
        # Disable word pairs
        collocations=False
    ).generate(text)

    # Create filename
    if video_id == None:
        temp_id = sql.set_temp_id()
        image_name = f'static/images/{temp_id}_wordcloud.png'
    else:
        image_name = f'static/images/{video_id}_wordcloud.png'

    if channel_title:
        title = channel_title
    else:
        title = video_id

    plt.figure(figsize = (FIG_W, FIG_H))
    plt.title(f'Nube de palabras más usadas para "{title}"', fontdict = {'fontsize' : TS})
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.savefig(image_name, dpi=100)

    return image_name

def split_sentiment_pos_neg(comment_sentiment):
    '''Divide los comentarios en positivos y negativos. Retorna un dataframe con todos los comentarios y dos dataframes con los comentarios positivos y negativos.'''

    comment_sentiment.sort_values(by='published_at', inplace=True)
    comment_sentiment['count'] = 1
    comment_sentiment['cumsum'] = comment_sentiment['count'].cumsum()

    # Seleccionar los comentarios positivos y negativos
    neg_sent = comment_sentiment[comment_sentiment['compound'] < -0.5]
    neg_sent['count'] = 1
    neg_sent['cumsum'] = neg_sent['count'].cumsum()
    pos_sent = comment_sentiment[comment_sentiment['compound'] > 0.5]
    pos_sent['count'] = 1
    pos_sent['cumsum'] = pos_sent['count'].cumsum()

    return comment_sentiment, pos_sent, neg_sent

def lineplot_cumsum_video_comments(comment_sentiment, video_id):
    '''Create and save a lineplot for the cumsum of video comments over time. Return image name.'''

    image_name = f'static/images/{video_id}_lineplot_cumsum_video_comments.png'

    plt.figure(figsize=(FIG_W, FIG_H))
    plt.plot(comment_sentiment['published_at'], comment_sentiment['cumsum'])
    plt.xticks(rotation=ROT)
    plt.title('Suma acumulada de comentarios a lo largo del tiempo', fontdict = {'fontsize' : TS})
    plt.xlabel('Fecha')
    plt.ylabel('Suma de Comentarios')
    plt.grid(True)
    plt.savefig(image_name, dpi=100)

    return image_name

def lineplot_cumsum_video_comments_pos_neg(comment_sentiment, pos_sent, neg_sent, video_id):
    '''Create and save a lineplot for the cumsum of positive and negative sentiments of video comments over time separately. Return image name.'''

    image_name = f'static/images/{video_id}_lineplot_cumsum_video_comments_pos_neg.png'

    plt.figure(figsize=(FIG_W, FIG_H))
    plt.plot('published_at', 'cumsum', data=pos_sent, marker='', color='green', linewidth=1, linestyle='-', label="Positive Sentiment")
    plt.plot('published_at', 'cumsum', data=neg_sent, marker='', color='red', linewidth=1, linestyle='-', label="Negative Sentiment")
    plt.legend()
    plt.title('Suma acumulada de comentarios a lo largo del tiempo', fontdict = {'fontsize' : TS})
    plt.xlabel('Fecha')
    plt.ylabel('Suma de Comentarios')
    plt.xticks(rotation=ROT)
    plt.grid(True)
    plt.savefig(image_name, dpi=100)

    return image_name

def scatterplot_sentiment_likecount(comment_sentiment, pos_sent, neg_sent, video_id):
    '''Create a scatterplot with like counts vs.sentiment. Save image.Return image name. Take as input the output of "split_sentiment_pos_neg()" and a video id.'''

    image_name = f'static/images/{video_id}_scatterplot_sentiment_likecount.png'

    fig = plt.figure(figsize=(FIG_W, FIG_H))
    plt.scatter(comment_sentiment['compound'], np.log1p(comment_sentiment['like_count']), label='Neutral Sentiment')
    plt.scatter(pos_sent['compound'], np.log1p(pos_sent['like_count']), color='green', label='Positive Sentiment')
    plt.scatter(neg_sent['compound'], np.log1p(neg_sent['like_count']), color='red', label='Negative Sentiment')
    plt.xticks(rotation=ROT)
    plt.title('Sentimientos / Contador de Likes', fontdict = {'fontsize' : TS})
    plt.xlabel('Sentimientos')
    plt.ylabel('Logaritmo del recuento de me gusta')
    plt.legend()
    plt.grid(True)
    fig.savefig(image_name, dpi=100)

    return image_name

def top_videos(video_df, metric='view', n=5):
    '''Return a table with top n videos of all channels in the dataframe considering a given metric. Possible metrics are like, dislike, comment and view'''

    df_table = video_df.sort_values(by=f'{metric}_count',ascending=False).groupby('channel_title').head(n).sort_values(by=f'{metric}_count', ascending=False)[['channel_title', 'title', f'{metric}_count']].rename(columns={'channel_title':'Channel Title', 'title':'Video Title', f'{metric}_count':f'{metric.capitalize()} Count'}).set_index('Channel Title')
    df_table = df_table.reset_index()
    df_table = df_table.set_index(df_table.index + 1)
    df_table = df_table.reset_index()
    df_table = df_table.rename(columns={'index':'Rank'})
    df_table = df_table.set_index(['Rank', 'Channel Title', 'Video Title',f'{metric.capitalize()} Count'])
    df_table.reset_index(inplace=True)

    return df_table

def get_channel_analysis_text(video_df, channel_titles, channel_ids, api_key):
    """
    Genera un análisis textual usando la API de ChatGPT en base a los datos de los canales y videos.
    """
    # Resumimos los datos principales para el prompt
    resumen = ""
    for channel_id, channel_title in zip(channel_ids, channel_titles):
        df_channel = video_df[video_df['channel_id'] == channel_id]
        total_videos = len(df_channel)
        total_views = int(df_channel['view_count'].sum())
        avg_views = int(df_channel['view_count'].mean()) if total_videos > 0 else 0
        avg_likes = int(df_channel['like_count'].mean()) if total_videos > 0 else 0
        resumen += f"Canal: {channel_title}\nVideos: {total_videos}\nVistas totales: {total_views}\nPromedio de vistas: {avg_views}\nPromedio de likes: {avg_likes}\n---\n"

    prompt = f"""
Eres un analista de datos de YouTube. A continuación tienes un resumen de datos de varios canales:
{resumen}
Redacta un análisis comparativo breve (máximo 150 palabras), resaltando diferencias, similitudes y cualquier dato relevante o curioso. Usa un tono profesional y claro.
Además necesito que envuelvas los datos extraidos de la API de YouTube (nombres de canal, cifras, etc.) en etiquetas tipo <strong> o <b> para que se destaquen en el análisis final.
Finalmente añade recomendaciones para los creadores de contenido basadas en los datos analizados y posibles tendencias a seguir.
"""

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    texto = response.choices[0].message.content.strip()
    return texto
