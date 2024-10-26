from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import json
import numpy as np
from urllib.parse import urlparse, parse_qs
import threading

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")  # 允许跨域

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/api/struct-tree', methods=['GET'])
def get_struct_tree():
    try:
        with open(os.path.join('static', 'Data', 'StructTree.json'), encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/channel-data', methods=['GET'])
def get_channel_data():
    try:
        path = request.args.get('path')
        if path:
            file_path = os.path.join('static', path.lstrip('/'))
            if os.path.exists(file_path):
                with open(file_path, encoding='utf-8') as f:
                    data = json.load(f)
                return jsonify(data)
            else:
                return jsonify({'error': 'File not found'}), 404
        else:
            return jsonify({'error': 'Path parameter is missing'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def filter_range(X_values, Y_values, time_begin, time_end, upper_bound, lower_bound):
    segments = []  # 用于保存符合条件的非连续段
    current_segment = {'X': [], 'Y': []}  # 当前的连续段

    for x, y in zip(X_values, Y_values):
        # 检查该点是否在时间和强度范围内
        if time_begin <= x <= time_end and lower_bound <= y <= upper_bound:
            # 如果在范围内，则添加到当前连续段
            current_segment['X'].append(x)
            current_segment['Y'].append(y)
        else:
            if current_segment['X']:
                segments.append(current_segment)
                current_segment = {'X': [], 'Y': []}  # 开始新的段

    if current_segment['X']:
        segments.append(current_segment)

    return segments

def merge_overlapping_intervals(intervals):
    if not intervals:
        return []
    # 按照 start_X 排序
    intervals.sort(key=lambda x: x['start_X'])
    merged = [intervals[0]]
    for current in intervals[1:]:
        prev = merged[-1]
        if current['start_X'] <= prev['end_X']:
            # 有重叠，合并
            prev['end_X'] = max(prev['end_X'], current['end_X'])
            # 更新相关系数为最大值
            prev['correlation'] = max(prev['correlation'], current['correlation'])
        else:
            merged.append(current)
    return merged

@app.route('/api/submit-data', methods=['POST'])
def submit_data():
    try:
        # 从请求中获取JSON数据
        data = request.get_json()

        selected_channels = data.get('selectedChannels')
        actual_points = data.get('actualPoints')
        time_begin = data.get('time_begin')
        time_end = data.get('time_end')
        upper_bound = data.get('upper_bound')
        lower_bound = data.get('lower_bound')

        # 处理 actual_points
        actual_X = actual_points['X']
        actual_Y = actual_points['Y']

        # 转换为 numpy 数组
        actual_X = np.array(actual_X)
        actual_Y = np.array(actual_Y)

        # 标准化处理 actual_Y
        actual_Y_std = (actual_Y - np.mean(actual_Y)) / (np.std(actual_Y) + 1e-8)  # 加上小值避免除零

        # 定义滑动窗口的最小和最大大小
        min_window_size = 10  # 可以根据需要调整最小窗口大小
        max_window_size = len(actual_Y_std)

        # 定义步长，增大步长以减少重叠
        step_size = max(1, max_window_size // 5)

        # 计算需要处理的总任务数
        total_tasks = 0
        for channel in selected_channels:
            parsed_url = urlparse(channel['path'])
            real_path = parse_qs(parsed_url.query).get('path', [None])[0]
            if real_path:
                file_path = os.path.join('static', real_path.lstrip('/'))
                if os.path.exists(file_path):
                    with open(file_path, encoding='utf-8') as f:
                        channel_data = json.load(f)
                    X_values = channel_data['X_value']
                    Y_values = channel_data['Y_value']
                    segments = filter_range(X_values, Y_values, time_begin, time_end, upper_bound, lower_bound)
                    for segment in segments:
                        segment_length = len(segment['Y'])
                        for window_size in range(min_window_size, min(max_window_size, segment_length) + 1):
                            total_tasks += max(0, (segment_length - window_size) // step_size + 1)

        if total_tasks == 0:
            return jsonify({"message": "No data to process"}), 200

        processed_tasks = 0  # 已处理的任务数
        matched_results = []  # 存储匹配结果

        # 定义一个函数用于处理数据并发送进度更新
        def process_data():
            nonlocal processed_tasks, matched_results

            last_progress = 0  # 上一次发送的进度值
            matched_results_per_channel = {}  # 存储每个通道的匹配结果

            for channel in selected_channels:
                matched_segments = []  # 当前通道的匹配段

                # 获取通道数据的真实路径
                parsed_url = urlparse(channel['path'])
                real_path = parse_qs(parsed_url.query).get('path', [None])[0]

                if real_path:
                    # 构造文件路径
                    file_path = os.path.join('static', real_path.lstrip('/'))

                    if os.path.exists(file_path):
                        with open(file_path, encoding='utf-8') as f:
                            channel_data = json.load(f)

                        # 获取通道数据的X和Y值
                        X_values = channel_data['X_value']
                        Y_values = channel_data['Y_value']

                        # 根据time_begin, time_end, upper_bound, lower_bound过滤数据
                        segments = filter_range(X_values, Y_values, time_begin, time_end, upper_bound, lower_bound)

                        # 如果通道在指定范围内没有数据，跳过该通道
                        if not segments:
                            continue

                        # 匹配算法
                        for segment in segments:
                            segment_X = np.array(segment['X'])
                            segment_Y = np.array(segment['Y'])

                            segment_length = len(segment_Y)

                            if segment_length < min_window_size:
                                continue

                            # 标准化处理 segment_Y
                            segment_Y_std = (segment_Y - np.mean(segment_Y)) / (np.std(segment_Y) + 1e-8)

                            # 滑动窗口匹配
                            for window_size in range(min_window_size, min(max_window_size, segment_length) + 1):
                                # 对实际曲线进行重采样
                                actual_Y_resampled = np.interp(
                                    np.linspace(0, 1, window_size),
                                    np.linspace(0, 1, len(actual_Y_std)),
                                    actual_Y_std
                                )

                                # 检查标准差是否为零，避免除以零的问题
                                if np.std(actual_Y_resampled) == 0:
                                    continue  # 如果标准差为零，则跳过

                                i = 0
                                while i <= segment_length - window_size:
                                    window_Y = segment_Y_std[i:i + window_size]

                                    # 如果标准差为零，跳过
                                    if np.std(window_Y) == 0:
                                        processed_tasks += 1
                                        i += step_size
                                        continue

                                    # 计算相关系数
                                    corr_coef = np.corrcoef(actual_Y_resampled, window_Y)[0, 1]

                                    # 如果 corr_coef 计算出现 NaN，跳过此段
                                    if np.isnan(corr_coef):
                                        processed_tasks += 1
                                        i += step_size
                                        continue

                                    # 增加已处理的任务数
                                    processed_tasks += 1

                                    # 计算并发送进度
                                    progress = int((processed_tasks / total_tasks) * 100)
                                    if progress != last_progress:
                                        last_progress = progress
                                        socketio.emit('progress', {'progress': progress})

                                    # 如果相关系数大于阈值，认为匹配
                                    threshold = 0.8
                                    if corr_coef >= threshold:
                                        # 保存匹配段的起始和结束 X 坐标
                                        matched_start_X = segment_X[i]
                                        matched_end_X = segment_X[i + window_size - 1]
                                        matched_segment = {
                                            'channel_name': channel['channel_name'],
                                            'start_X': matched_start_X,
                                            'end_X': matched_end_X,
                                            'correlation': corr_coef
                                        }
                                        matched_segments.append(matched_segment)

                                        # 跳过已匹配的窗口，避免重叠
                                        i += window_size
                                    else:
                                        i += step_size

                        # 合并当前通道的重叠匹配段
                        merged_segments = merge_overlapping_intervals(matched_segments)
                        matched_results_per_channel[channel['channel_name']] = merged_segments

            # 收集所有通道的匹配结果
            matched_results = []
            for channel_name, segments in matched_results_per_channel.items():
                for segment in segments:
                    segment['channel_name'] = channel_name
                    matched_results.append(segment)

            # 处理完成后，将匹配结果直接发送到前端
            socketio.emit('matched_results', {'matched_results': matched_results})

            # 文件写入完成，发送100%进度
            socketio.emit('progress', {'progress': 100})

        # 启动一个线程来处理数据
        threading.Thread(target=process_data).start()

        return jsonify({"message": "Data processing started"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app)
