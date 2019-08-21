#!/usr/bin/env python
# coding: utf-8

import requests
from collections import defaultdict
import json
import re
from scrapChat import afre_chat, twi_chat
import pandas as pd
from download import download


def afreeca_get_video_urls(bj_id):
    """
    아프리카 비제이의 영상 url들을 파싱해오는 함수 입니다.

    :param bj_id: bj의 아이디 입니다.(닉네임x)
    :return: 아프리카 비제이의 영상 url (/123453형식)을 반환합니다.
    """
    url='http://bjapi.afreecatv.com/api/'+bj_id+'/vods'
    video_list = []
    i = 1
    while True:
        param = {'page':i}
        result = download('get', url, param=param).json()['data']
        if not result:
            break
        video_list.extend(["/"+str(_['title_no']) for _ in result])
        i += 1
    return video_list


# In[74]:

def get_video_urls(bj_id, platform):
    """
    플랫폼별로 불러오는 방식이 달라 bj_id와 platform을 입력하면 그에 맞춰 처리해줍니다.
    :param bj_id: bj_id
    :param platform: 플랫폼 이름(영어)를 넣어주세요
    :return: bj의 영상 url들을 반환해줍니다.
    """
    if platform == 'afreeca':
        return afreeca_get_video_urls(bj_id)
    elif platform == 'twitch':
        return twitch_get_video_urls(bj_id)
    else:
        return


def parse_url(bjList):
    """
    비제이들의 영상 url 목록들을 파싱하는 함수
    
    Parameters
    ----------
    bjList : list형태, 영상 링크들을 파싱해오고 싶은 비제이 아이디가 들어있는 리스트
    get_video_urls : function, 파싱하고 싶은 사이트의 url을 파싱해오는 함수

    :return: {'bj_id':['/urls',...]} dict형식으로 여러 bj들의 url list를 반환해줍니다.
    """
    urldict = defaultdict(list)
    for bj_id, platform in bjList:
        vUrls = get_video_urls(bj_id, platform)
        urldict[bj_id] = vUrls
        print('1명꺼 끝!')
    return urldict


# In[75]:


def twitch_get_video_urls(bj_id):
    '''
    트위치 bj의 영상 url을 불러옵니다.
    :param bj_id:
    :return: list, 파싱한 url들이 담긴 list를 반환한다.
    '''
    urls = []
    offset = 0
    while True:
        url = "https://api.twitch.tv/kraken/channels/" + bj_id + "/videos"
        params = {
            'broadcast_type': 'archive',
            'limit': 100,
            'offset': offset
        }
        html = download('get', url, param=params).json()
        if not 'videos' in html.keys() or len(html['videos']) == 0:
            break

        urls.extend([_['url'] for _ in html['videos']])
        offset = re.search(r'offset=(\d*)', html['_links']['next']).group(1)
    return [re.search(r'videos(/\d+)', url).group(1) for url in urls]


def afreeca_make_datasets(bj_id, urls, n=3):
    '''
    파싱해온 urls를 넣으면 영상 3개에서 chatingdata를 뽑아온다.
    :param bj_id: str
    :param urls: list, url = '/123345'
    :param n: 채팅 데이터를 스크래핑할 영상 개수 default = 3
    :return: DataFrame, columns = [0, 1, 2] : (comment, writer, time)
    '''
    result = pd.DataFrame()
    for _ in urls[:n]:
        url = 'http://vod.afreecatv.com/PLAYER/STATION' + _
        chatdata = pd.DataFrame(afre_chat(url))
        result = pd.concat([result, chatdata])

    return result.reset_index()


def twitch_make_datasets(bj_id, urls, n=3):
    '''
    트위치 영상 채팅 데이터 스크래핑 하는 함수
    :param bj_id: str, bj 아이디
    :param urls: list, '/123435'형태의 url이 들어있는 list
    :param n: int, 스크래핑 하고 싶은 영상 개수 (default=3)
    :return: DataFrame, columns = [0, 1, 2] : (comment, writer, time)
    '''
    result = pd.DataFrame()
    for _ in urls[:n]:
        chatdata = pd.DataFrame(twi_chat(_))
        result = pd.concat([result, chatdata])

    return result.reset_index()

def make_dataset(bj_id, urls, platform, n=3):
    '''
    플랫폼을 같이 받아서 데이터 셋을 만들어주는 함수
    :param bj_id: str, bj 아이디
    :param urls: list, '/123435'형태의 url이 들어있는 list
    :param platform: str,
    :param n: int, 스크래핑 하고 싶은 영상 개수 (default=3)
    :return: DataFrame, columns = [0, 1, 2] : (comment, writer, time)
    '''
    print('platform = ', platform)
    if platform =='afreeca':
        return afreeca_make_datasets(bj_id, urls, n)
    elif platform =='twitch':
        return twitch_make_datasets(bj_id, urls, n)
    else :
        print('여기는 유튜브임')
        return