$(document).ready(function() {
    let serviceId = null;
    let statsInterval = null;
    
    // 监听源类型变化
    $('#source-type').change(function() {
        if ($(this).val() === 'camera') {
            $('#camera-selector').show();
            $('#video-selector').hide();
        } else {
            $('#camera-selector').hide();
            $('#video-selector').show();
            loadVideoFiles();
        }
    });
    
    // 加载视频文件列表
    function loadVideoFiles() {
        $.get('/api/fileList', function(data) {
            const videoSelect = $('#video-file');
            videoSelect.empty();
            
            data.file_list.forEach(file => {
                videoSelect.append($('<option>', {
                    value: file,
                    text: file
                }));
            });
        }).fail(function() {
            alert('加载视频文件列表失败');
        });
    }
    
    // 开始检测按钮
    $('#start-btn').click(function() {
        startDetection();
    });
    
    // 停止检测按钮
    $('#stop-btn').click(function() {
        stopDetection();
    });
    
    // 开始检测
    function startDetection() {
        // 默认透视变换源点（可能需要根据实际场景调整）
        const srcPoints = [
            { x: 200, y: 500 },
            { x: 440, y: 500 },
            { x: 120, y: 850 },
            { x: 660, y: 850 }
        ];
        
        // 在startDetection函数中修改这部分代码
        // 确定源类型和路径
        let capType, capPath;
        if ($('#source-type').val() === 'camera') {
            capType = 'camera'; // 修改为'camera'类型
            capPath = $('#camera-id').val();
        } else {
            capType = 'file';
            capPath = $('#video-file').val();
        }
        
        // 发送开始检测请求
        $.ajax({
            url: '/api/start',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                src_points: srcPoints,
                cap_type: capType,
                cap_path: capPath
            }),
            success: function(data) {
                serviceId = data.service_id;
                console.log('开始检测，服务ID:', serviceId);
                
                // 更新UI状态
                $('#start-btn').prop('disabled', true);
                $('#stop-btn').prop('disabled', false);
                
                // 开始显示视频流
                updateVideoStreams();
                
                // 开始更新统计信息
                startStatsUpdate();
            },
            error: function(xhr) {
                alert('开始检测失败: ' + xhr.responseJSON.error);
            }
        });
    }
    
    // 停止检测
    function stopDetection() {
        if (serviceId === null) return;
        
        $.get('/api/release/' + serviceId, function() {
            console.log('停止检测，服务ID:', serviceId);
            
            // 清除视频流
            $('#raw-video').attr('src', '');
            $('#processed-video').attr('src', '');
            $('#birdview-video').attr('src', '');
            
            // 停止更新统计信息
            stopStatsUpdate();
            
            // 重置统计信息
            resetStats();
            
            // 更新UI状态
            $('#start-btn').prop('disabled', false);
            $('#stop-btn').prop('disabled', true);
            
            serviceId = null;
        }).fail(function() {
            alert('停止检测失败');
        });
    }
    
    // 更新视频流
    function updateVideoStreams() {
        if (serviceId === null) return;
        
        // 设置视频流URL（添加时间戳防止缓存）
        const timestamp = new Date().getTime();
        $('#raw-video').attr('src', '/api/getRowFrame/' + serviceId + '?' + timestamp);
        $('#processed-video').attr('src', '/api/getProcessedFrame/' + serviceId + '?' + timestamp);
        $('#birdview-video').attr('src', '/api/getBirdViewFrame/' + serviceId + '?' + timestamp);
        
        // 每30毫秒更新一次（大约33fps）
        setTimeout(updateVideoStreams, 30);
    }
    
    // 开始更新统计信息
    function startStatsUpdate() {
        // 每秒更新一次统计信息
        statsInterval = setInterval(updateStats, 1000);
    }
    
    // 停止更新统计信息
    function stopStatsUpdate() {
        if (statsInterval !== null) {
            clearInterval(statsInterval);
            statsInterval = null;
        }
    }
    
    // 更新统计信息
    function updateStats() {
        if (serviceId === null) return;
        
        $.ajax({
            url: '/api/getStatistics/' + serviceId,
            type: 'POST',
            success: function(data) {
                const stats = data.statistics;
                
                // 更新基本统计信息
                $('#total-count').text(stats.total_count);
                $('#long-stay-count').text(stats.long_stay_count);
                $('#crossing-count').text(stats.crossing_count);
                
                // 更新类别统计信息
                const categoryList = $('#category-list');
                categoryList.empty();
                
                Object.entries(stats.category_count).forEach(([category, count]) => {
                    categoryList.append(`<div class="category-item">${category}: ${count}</div>`);
                });
            },
            error: function() {
                console.error('更新统计信息失败');
            }
        });
    }
    
    // 重置统计信息
    function resetStats() {
        $('#total-count').text('0');
        $('#long-stay-count').text('0');
        $('#crossing-count').text('0');
        $('#category-list').empty();
    }
    
    // 页面关闭时停止服务
    $(window).on('beforeunload', function() {
        if (serviceId !== null) {
            // 发送停止请求但不等待响应
            $.ajax({
                url: '/api/release/' + serviceId,
                type: 'GET',
                async: false
            });
        }
    });
});