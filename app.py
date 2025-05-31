from flask import Flask, render_template, request
from src import youtube_data_module as ydt
from src import viz
import pandas as pd
import os
import logging
import sys

logger = logging.getLogger('app_logger')
handler = logging.StreamHandler(sys.stderr)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# API_KEY = os.getenv('YOUTUBE_API_KEY')
API_KEY = "AIzaSyCR6BEEh5S3OPChro6KjJBsQ30qVETd7GE"
# API_KEY = "AIzaSyBmRKUAfBUn66IA-sQDbXf50hWQvuheCfs"

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('layout.html')

@app.route('/select_video')
def select_video():
    '''This page returns search results, when a user hits the 'Search Video' button'''
    result_dictionary = request.args
    query = result_dictionary['query']
    youtube = ydt.youtubeAPIkey(API_KEY)
    query_result = ydt.youtubeSearchListStatistics(youtube, q=query)

    return render_template(
        'select_video.html',
        query_result=query_result,
        query=query
    )

@app.route('/video_comments')
def video_comments():
    '''This page returns a video comment analysis, when a user hits the 'See video comment analysis' button'''
    video_id = request.args.get('video_id')

    youtube = ydt.youtubeAPIkey(API_KEY)

    logger.info('Getting all comments')
    all_snippets = ydt.get_all_comments(youtube, video_id)
    logger.info('Writing comments to dict')
    comment_dict = ydt.extract_comments(all_snippets) # Based on this comment_dict, we can generate a wordcloud and ask chatGPT to generate an analysis

    image_names = []
    logger.info('Generating wordcloud')
    comment_string = ydt.concat_comments(comment_dict)
    video_title = video_id
    image_names.append(viz.create_wordcloud(comment_string, stopwords=None, video_id=video_id, channel_title=video_title))
    comment_df = ydt.comments_to_df(all_snippets)
    comment_sentiment = ydt.analyze_comment_sentiments(comment_df)
    comment_sentiment2, pos_sent, neg_sent = viz.split_sentiment_pos_neg(comment_sentiment)
    image_names.append(viz.lineplot_cumsum_video_comments(comment_sentiment2, video_id))
    image_names.append(viz.lineplot_cumsum_video_comments_pos_neg(comment_sentiment2, pos_sent, neg_sent, video_id))
    image_names.append(viz.scatterplot_sentiment_likecount(comment_sentiment2, pos_sent, neg_sent, video_id))
    # Asegurando que la columna 'like_count' sea numérica
    comment_sentiment2['like_count'] = pd.to_numeric(comment_sentiment2['like_count'], errors='coerce')
    
    # Check the actual sentiment column names in the DataFrame
    actual_sentiment_columns = [col for col in comment_sentiment2.columns if 'sentiment' in col]
    
    for col in actual_sentiment_columns:
        comment_sentiment2[col] = pd.to_numeric(comment_sentiment2[col], errors='coerce')

    # Borrando filas con valores NaN en 'like_count' y las columnas de sentimiento
    comment_sentiment2 = comment_sentiment2.dropna(subset=['like_count'] + actual_sentiment_columns)

    # Calcular la correlación entre 'like_count' y las columnas de sentimiento
    try:
        like_count_sentiment_corr = round(comment_sentiment2.corr().loc['like_count'][actual_sentiment_columns[0]], 2)
    except KeyError as e:
        logger.error(f"KeyError: {e}")
        like_count_sentiment_corr = None
    except ValueError as e:
        logger.error(f"ValueError: {e}")
        like_count_sentiment_corr = None

    return render_template(
        'video_comments.html',
        image_names=image_names,
        like_count_sentiment_corr=like_count_sentiment_corr
    )

@app.route('/select_channels', methods=['GET', 'POST'])
def select_channels():
    result_dictionary = request.args
    channel_names = []

    for channel_name in result_dictionary:
        if len(result_dictionary.get(channel_name)) > 0:
            channel_names.append(result_dictionary[channel_name])

    # Si está en modo desarrollo, usar datos simulados
    if os.environ.get("FLASK_ENV") == "development":
        query_results = {
            "Canal 1": {
                "items": [
                    {
                        "snippet": {
                            "channelId": "UC123",
                            "title": "Canal de Prueba 1",
                            "thumbnails": {
                                "medium": {"url": "https://placehold.co/400"}
                            }
                        }
                    }
                ]
            },
            "Canal 2": {
                "items": [
                    {
                        "snippet": {
                            "channelId": "UC456",
                            "title": "Canal de Prueba 2",
                            "thumbnails": {
                                "medium": {"url": "https://placehold.co/400"}
                            }
                        }
                    }
                ]
            }
        }
    else:
        youtube = ydt.youtubeAPIkey(API_KEY)
        query_results = {}
        for cn in channel_names:
            result = ydt.youtubeSearchList(youtube, channel_id=None, q=cn, maxResults=5, type='channel')
            query_results[cn] =  result

    return render_template(
        'select_channels.html',
        query_results=query_results
    )

@app.route('/channels', methods=['GET', 'POST'])
def channels():
    '''Esta página retorna el análisis de comparación de canales cuando el usuario selecciona al menos dos canales y presiona "Comparar canales ahora"'''
    result_dictionary = request.args

    channel_ids = []
    for c_id in result_dictionary:
        if len(result_dictionary[c_id]) == 24:
            channel_ids.append(result_dictionary[c_id])

    channel_thumbnails = []

    # Si está en modo desarrollo, cargar imágenes y tabla de ejemplo
    if os.environ.get("FLASK_ENV") == "development":
        # Puedes personalizar estos nombres de imagen según los archivos que tengas en static/images
        image_names = [
            'static/images/UC4FHiPgS1KXkUMx3dxBUtPg_UCxPD7bsocoAMq8Dj18kmGyQ_barplot_channel_video_count.png',
            'static/images/UC4FHiPgS1KXkUMx3dxBUtPg_UCxPD7bsocoAMq8Dj18kmGyQ_barplot_links.png',
            'static/images/UCxPD7bsocoAMq8Dj18kmGyQ_histogram_video_duration_count.png',
            'static/images/UCxPD7bsocoAMq8Dj18kmGyQ_wordcloud.png',
            'static/images/UC4FHiPgS1KXkUMx3dxBUtPg_histogram_video_duration_count.png',
            'static/images/UC4FHiPgS1KXkUMx3dxBUtPg_wordcloud.png',
        ]
        # Tabla de ejemplo
        import pandas as pd
        df_table = pd.DataFrame({
            'Posición': [1, 2],
            'Nombre del Canal': ['Canal de Prueba 1', 'Canal de Prueba 2'],
            'Título del video': ['Video 1', 'Video 2'],
            'Número de vistas': [10000, 8000]
        })
        tables = [df_table.to_html(index=False, classes='table-striped')]
        channel_titles = ['Canal de Prueba 1', 'Canal de Prueba 2']
        # Thumbnails de ejemplo
        channel_thumbnails = ["https://placehold.co/120x120", "https://placehold.co/120x120"]
    else:
        youtube = ydt.youtubeAPIkey(API_KEY)
        video_df = ydt.get_channel_video_df(youtube, channel_ids)

        image_names = []
        image_names.append(viz.barplot_channel_video_count(video_df, channel_ids))
        image_names.append(viz.barplot_links(video_df, channel_ids))

        channel_titles = []
        channel_thumbnails = []
        for channel_id in channel_ids:
            channel_video_df = video_df[video_df['channel_id'] == channel_id]
            channel_title = channel_video_df['channel_title'].unique()[0]
            channel_titles.append(channel_title)
            # Obtener thumbnail real del canal
            try:
                channel_info = youtube.channels().list(part="snippet", id=channel_id).execute()
                thumb_url = channel_info['items'][0]['snippet']['thumbnails']['medium']['url']
            except Exception:
                thumb_url = "https://placehold.co/120x120"
            channel_thumbnails.append(thumb_url)
            image_names.append(viz.histogram_video_duration_count_single(channel_video_df, channel_id, channel_title=channel_title))
            channel_video_series = channel_video_df['tags']
            wordcloud_string = ydt.concat_listelements(channel_video_series)
            image_names.append(viz.create_wordcloud(wordcloud_string, stopwords=None, video_id=channel_id, channel_title=channel_title))

        df_table = viz.top_videos(video_df, metric='view', n=5)
        tables = [df_table.to_html(index=False, classes='table-striped')]

    
    analysis_text = None
    try:
        import openai
        if OPENAI_API_KEY and len(channel_titles) > 0:
            analysis_text = viz.get_channel_analysis_text(video_df, channel_titles, channel_ids, OPENAI_API_KEY)
    except Exception as e:
        logger.error(f"Error al generar análisis con ChatGPT: {e}")
        analysis_text = None

    return render_template(
        'channels.html',
        result_dictionary=result_dictionary,
        image_names=image_names,
        channel_ids=channel_ids,
        channel_titles=channel_titles,
        channel_thumbnails=channel_thumbnails,
        tables=tables,
        analysis_text=analysis_text,
    )

if __name__ == '__main__':
    app.run(port=3000, debug=True)
