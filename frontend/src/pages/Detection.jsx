import { useState, useRef, useEffect } from 'react';
import { Upload, Camera, Video, AlertTriangle, X, Loader2, Image as ImageIcon, Wifi, WifiOff, Play, Square } from 'lucide-react';
import { detectionAPI } from '../services/api';
import toast from 'react-hot-toast';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
// WebSocket connects to ws://localhost:8000 (no /api/v1 prefix)
const BASE_WS_URL = 'ws://localhost:8000';

export default function Detection() {
  const [mode, setMode] = useState('image'); // 'image', 'realtime', 'video'
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [videoFile, setVideoFile] = useState(null);
  const [videoPreview, setVideoPreview] = useState('');
  const [videoResult, setVideoResult] = useState(null);
  
  // Realtime states
  const [isStreaming, setIsStreaming] = useState(false);
  const [ws, setWs] = useState(null);
  const [realtimeStats, setRealtimeStats] = useState({
    totalWeapons: 0,
    withPerson: 0,
    fps: 0
  });
  
  const fileInputRef = useRef(null);
  const videoInputRef = useRef(null);
  const videoRef = useRef(null);
  const videoPlaybackRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const wsRef = useRef(null);
  const frameIntervalRef = useRef(null);
  const animationFrameRef = useRef(null);
  const detectionDataRef = useRef(null);
  const isStreamingRef = useRef(false);
  const isProcessingRef = useRef(false); // Ping-Pong control flag

  useEffect(() => {
    return () => {
      stopStreaming();
    };
  }, []);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        toast.error('Vui lòng chọn file hình ảnh');
        return;
      }
      
      setSelectedFile(file);
      setResult(null);
      
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleVideoSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.type.startsWith('video/')) {
        toast.error('Vui lòng chọn file video');
        return;
      }
      
      setVideoFile(file);
      setResult(null);
      setVideoResult(null);
      
      const url = URL.createObjectURL(file);
      setVideoPreview(url);
      
      toast.success('Video đã sẵn sàng! Nhấn "Bắt đầu phát hiện" để xử lý real-time');
    }
  };

  const handleVideoReset = () => {
    // Stop streaming first
    if (isStreaming) {
      stopStreaming();
    }
    
    setVideoFile(null);
    setVideoPreview('');
    setVideoResult(null);
    setRealtimeStats({ totalWeapons: 0, withPerson: 0, fps: 0 });
    
    if (videoInputRef.current) {
      videoInputRef.current.value = '';
    }
    if (videoPreview) {
      URL.revokeObjectURL(videoPreview);
    }
    
    // Reset video element
    if (videoPlaybackRef.current) {
      videoPlaybackRef.current.pause();
      videoPlaybackRef.current.currentTime = 0;
    }
  };

  const handleDetect = async () => {
    if (!selectedFile) {
      toast.error('Vui lòng chọn hình ảnh');
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('confidence', '0.5');
      formData.append('model_type', 'yolo');

      const response = await detectionAPI.detectWeaponWithPairing(formData);
      setResult(response);
      
      if (response.pairs && response.pairs.length > 0) {
        toast.success(`Phát hiện ${response.total_weapons} vũ khí!`);
      } else {
        toast.success('Không phát hiện vũ khí trong ảnh');
      }
    } catch (error) {
      console.error('Detection error:', error);
      toast.error('Phát hiện thất bại: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const startWebcam = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: 640, height: 480 } 
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
        
        // Wait for video to be ready
        videoRef.current.onloadedmetadata = async () => {
          if (canvasRef.current && videoRef.current) {
            const canvas = canvasRef.current;
            const video = videoRef.current;
            
            // Play video
            await video.play();
            
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            // Start continuous rendering loop
            startRenderLoop(video, canvas);
          }
        };
      }
      
      toast.success('Webcam đã sẵn sàng');
    } catch (error) {
      console.error('Webcam error:', error);
      toast.error('Không thể truy cập webcam');
    }
  };

  const startRenderLoop = (videoSource, canvas) => {
    const renderLoop = () => {
      if (videoSource && videoSource.readyState === videoSource.HAVE_ENOUGH_DATA && canvas) {
        const ctx = canvas.getContext('2d');
        
        // Always draw the fresh video frame first
        ctx.drawImage(videoSource, 0, 0, canvas.width, canvas.height);
        
        // Draw detection boxes on top if we have data
        if (detectionDataRef.current && detectionDataRef.current.detections) {
          drawDetections(ctx, detectionDataRef.current.detections, canvas.width, canvas.height);
        }
      }
      
      // Continue loop
      animationFrameRef.current = requestAnimationFrame(renderLoop);
    };
    renderLoop();
  };

  const drawDetections = (ctx, detections, canvasWidth, canvasHeight) => {
    detections.forEach(det => {
      const { x1, y1, x2, y2 } = det.bbox;
      const width = x2 - x1;
      const height = y2 - y1;
      
      // Draw red bounding box
      ctx.strokeStyle = '#ff0000';
      ctx.lineWidth = 3;
      ctx.strokeRect(x1, y1, width, height);
      
      // Draw label background
      const label = `${det.class_name} ${(det.confidence * 100).toFixed(0)}%`;
      ctx.font = 'bold 16px Arial';
      const textMetrics = ctx.measureText(label);
      const textHeight = 20;
      
      ctx.fillStyle = '#ff0000';
      ctx.fillRect(x1, y1 - textHeight - 5, textMetrics.width + 10, textHeight + 5);
      
      // Draw label text
      ctx.fillStyle = '#ffffff';
      ctx.fillText(label, x1 + 5, y1 - 8);
    });
  };

  const startStreaming = async () => {
    if (isStreaming) return;
    
    // Check if we're in video mode with uploaded video
    if (mode === 'video') {
      // Video mode: Use uploaded video file
      if (!videoPlaybackRef.current || !videoPreview) {
        toast.error('Vui lòng chọn video trước');
        return;
      }
      
      // Start video playback
      try {
        await videoPlaybackRef.current.play();
        toast.success('Bắt đầu xử lý video real-time!');
      } catch (error) {
        console.error('Video play error:', error);
        toast.error('Không thể phát video');
        return;
      }
    } else {
      // Realtime webcam mode
      if (!streamRef.current) {
        await startWebcam();
      }
    }
    
    // Connect WebSocket
    const token = localStorage.getItem('token');
    const wsConnection = new WebSocket(`${BASE_WS_URL}/api/v1/realtime/ws/realtime-detect?token=${token}&confidence=0.5&model_type=yolo`);
    
    wsConnection.onopen = () => {
      console.log('WebSocket connected');
      toast.success('Kết nối thành công!');
      setIsStreaming(true);
      isStreamingRef.current = true;
      isProcessingRef.current = false;
      
      // Ping-Pong: Kick-start the loop with first frame
      sendFrame(wsConnection);
    };
    
    wsConnection.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        console.log('📦 Received from backend:', {
          total_weapons: data.total_weapons,
          detections_count: data.detections?.length || 0
        });
        
        if (data.error) {
          console.error('WebSocket error:', data.error);
          toast.error('Lỗi: ' + data.error);
          isProcessingRef.current = false;
          return;
        }
        
        // Update stats
        setRealtimeStats({
          totalWeapons: data.total_weapons || 0,
          withPerson: 0,
          fps: data.processing_time ? (1 / data.processing_time).toFixed(1) : 0
        });
        
        // Store detection data for rendering
        detectionDataRef.current = data;
        
        // Ping-Pong: Mark as done processing, allow next frame
        isProcessingRef.current = false;
        
        // Immediately request next frame (creates continuous loop without backpressure)
        requestAnimationFrame(() => sendFrame(wsConnection));
      } catch (error) {
        console.error('Parse error:', error);
        isProcessingRef.current = false;
      }
    };
    
    wsConnection.onerror = (error) => {
      console.error('WebSocket error:', error);
      toast.error('Lỗi kết nối WebSocket');
    };
    
    wsConnection.onclose = () => {
      console.log('WebSocket closed');
      setIsStreaming(false);
      isStreamingRef.current = false;
      isProcessingRef.current = false;
      
      // Pause video if in video mode
      if (mode === 'video' && videoPlaybackRef.current) {
        videoPlaybackRef.current.pause();
      }
    };
    
    wsRef.current = wsConnection;
    setWs(wsConnection);
  };

  const sendFrame = (wsConnection) => {
    // Ping-Pong: Only send if streaming, socket open, AND not processing
    if (!isStreamingRef.current || !wsConnection || 
        wsConnection.readyState !== WebSocket.OPEN || isProcessingRef.current) {
      return;
    }
    
    try {
      let videoSource;
      
      // Choose video source based on mode
      if (mode === 'video') {
        videoSource = videoPlaybackRef.current; // Video file
        
        // Check if video ended
        if (videoSource && videoSource.ended) {
          toast.success('Video đã kết thúc!');
          stopStreaming();
          return;
        }
      } else {
        videoSource = videoRef.current; // Webcam
      }
      
      // Check if video source is ready
      if (!videoSource || !videoSource.videoWidth || !videoSource.videoHeight || videoSource.readyState < 2) {
        // Retry in next frame
        requestAnimationFrame(() => sendFrame(wsConnection));
        return;
      }
      
      // Create canvas to capture and resize frame
      const canvas = document.createElement('canvas');
      const aspectRatio = videoSource.videoHeight / videoSource.videoWidth;
      canvas.width = 640;
      canvas.height = Math.floor(640 * aspectRatio);
      
      const ctx = canvas.getContext('2d');
      ctx.drawImage(videoSource, 0, 0, canvas.width, canvas.height);
      
      // Lower quality to 0.7 for faster transfer
      const frameData = canvas.toDataURL('image/jpeg', 0.7);
      
      wsConnection.send(JSON.stringify({ frame: frameData }));
      
      // Ping-Pong: Mark as busy, don't send more until server responds
      isProcessingRef.current = true;
    } catch (error) {
      console.error('❌ Send frame error:', error);
      isProcessingRef.current = false;
      
      // Retry in next frame
      requestAnimationFrame(() => sendFrame(wsConnection));
    }
  };

  const stopStreaming = () => {
    if (frameIntervalRef.current) {
      clearInterval(frameIntervalRef.current);
    }
    
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    // Stop webcam only in realtime mode
    if (mode === 'realtime' && streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    // Pause video in video mode
    if (mode === 'video' && videoPlaybackRef.current) {
      videoPlaybackRef.current.pause();
    }
    
    setIsStreaming(false);
    isStreamingRef.current = false;
    isProcessingRef.current = false;
    setWs(null);
    
    // Clear detection data
    detectionDataRef.current = null;
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPreview('');
    setResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getDangerColor = (level) => {
    switch (level) {
      case 'high': return 'bg-red-500/20 text-red-400 border-red-500/50';
      case 'medium': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
      case 'low': return 'bg-green-500/20 text-green-400 border-green-500/50';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/50';
    }
  };

  const getDangerLabel = (level) => {
    switch (level) {
      case 'high': return 'Nguy hiểm cao';
      case 'medium': return 'Nguy hiểm trung bình';
      case 'low': return 'Nguy hiểm thấp';
      default: return level;
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
          <Camera className="w-8 h-8 text-blue-400" />
          Phát hiện vũ khí
        </h1>
        <p className="text-gray-400">
          Upload ảnh, video hoặc sử dụng webcam để phát hiện vũ khí realtime
        </p>
      </div>

      {/* Mode Selector */}
      <div className="mb-6 flex gap-3">
        <button
          onClick={() => { setMode('image'); stopStreaming(); }}
          className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold transition ${
            mode === 'image' 
              ? 'bg-blue-600 text-white' 
              : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
          }`}
        >
          <ImageIcon className="w-5 h-5" />
          Ảnh tĩnh
        </button>
        
        <button
          onClick={() => { setMode('realtime'); setResult(null); }}
          className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold transition ${
            mode === 'realtime' 
              ? 'bg-blue-600 text-white' 
              : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
          }`}
        >
          <Camera className="w-5 h-5" />
          Webcam Realtime
        </button>
        
        <button
          onClick={() => { setMode('video'); stopStreaming(); handleVideoReset(); }}
          className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold transition ${
            mode === 'video' 
              ? 'bg-blue-600 text-white' 
              : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
          }`}
        >
          <Video className="w-5 h-5" />
          Video Upload
        </button>
      </div>

      {/* Image Mode */}
      {mode === 'image' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Upload Section */}
          <div className="space-y-4">
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
              <h2 className="text-xl font-semibold text-white mb-4">Tải ảnh lên</h2>

              {!preview ? (
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-slate-600 rounded-xl p-12 text-center hover:border-blue-500 hover:bg-slate-700/30 transition cursor-pointer"
                >
                  <ImageIcon className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                  <p className="text-gray-300 mb-2">Click để chọn ảnh</p>
                  <p className="text-gray-500 text-sm">Hỗ trợ: JPG, PNG, JPEG</p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="relative rounded-xl overflow-hidden border border-slate-600">
                    <img src={preview} alt="Preview" className="w-full h-auto" />
                    <button
                      onClick={handleReset}
                      className="absolute top-2 right-2 p-2 bg-red-500/80 hover:bg-red-600 rounded-lg transition"
                    >
                      <X className="w-5 h-5 text-white" />
                    </button>
                  </div>

                  <div className="flex gap-3">
                    <button
                      onClick={handleDetect}
                      disabled={loading}
                      className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin" />
                          Đang phát hiện...
                        </>
                      ) : (
                        <>
                          <Camera className="w-5 h-5" />
                          Phát hiện
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Results Section */}
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <h2 className="text-xl font-semibold text-white mb-4">Kết quả</h2>

            {!result ? (
              <div className="text-center py-16">
                <Camera className="w-20 h-20 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400">Chưa có kết quả</p>
              </div>
            ) : (
              <div className="space-y-4">
                {result.image_url && (
                  <img 
                    src={`http://localhost:8000${result.image_url}`} 
                    alt="Result" 
                    className="w-full rounded-lg border border-slate-600" 
                  />
                )}

                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-700/30 rounded-lg p-4">
                    <p className="text-gray-400 text-sm">Tổng vũ khí</p>
                    <p className="text-2xl font-bold text-white">{result.total_weapons}</p>
                  </div>
                  <div className="bg-slate-700/30 rounded-lg p-4">
                    <p className="text-gray-400 text-sm">Người cầm</p>
                    <p className="text-2xl font-bold text-yellow-400">{result.weapons_with_persons}</p>
                  </div>
                </div>

                {result.pairs && result.pairs.map((pair, idx) => (
                  <div key={idx} className={`border rounded-lg p-4 ${getDangerColor(pair.danger_level)}`}>
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-bold">{pair.weapon.class_name}</p>
                        <p className="text-sm">{getDangerLabel(pair.danger_level)}</p>
                        <p className="text-xs mt-1">
                          {pair.status === 'held_by_person' ? '👤 Người cầm' : '⚠️ Không người cầm'}
                        </p>
                      </div>
                      <p className="text-2xl font-bold">
                        {(pair.weapon.confidence * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Realtime Mode */}
      {mode === 'realtime' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Video Stream */}
          <div className="lg:col-span-2 bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-white">Webcam Stream</h2>
              <div className="flex items-center gap-2">
                {isStreaming ? (
                  <Wifi className="w-5 h-5 text-green-400 animate-pulse" />
                ) : (
                  <WifiOff className="w-5 h-5 text-gray-500" />
                )}
                <span className={`text-sm ${isStreaming ? 'text-green-400' : 'text-gray-500'}`}>
                  {isStreaming ? 'Đang phát' : 'Chưa kết nối'}
                </span>
              </div>
            </div>

            <div className="relative bg-black rounded-lg overflow-hidden flex items-center justify-center" style={{ height: '480px' }}>
              {/* Original video (hidden, only used as source) */}
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="hidden"
              />
              
              {/* Canvas overlay for video + detection boxes */}
              <canvas
                ref={canvasRef}
                className="max-w-full max-h-full object-contain"
              />
              
              {!streamRef.current && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <Camera className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-400">Nhấn Start để bắt đầu</p>
                  </div>
                </div>
              )}
            </div>

            <div className="mt-4 flex gap-3">
              {!isStreaming ? (
                <button
                  onClick={startStreaming}
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition flex items-center justify-center gap-2"
                >
                  <Play className="w-5 h-5" />
                  Bắt đầu phát hiện
                </button>
              ) : (
                <button
                  onClick={stopStreaming}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white font-semibold py-3 px-6 rounded-lg transition flex items-center justify-center gap-2"
                >
                  <Square className="w-5 h-5" />
                  Dừng lại
                </button>
              )}
            </div>
          </div>

          {/* Realtime Stats */}
          <div className="space-y-4">
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Thống kê Realtime</h3>
              
              <div className="space-y-4">
                <div className="bg-gradient-to-r from-red-600/20 to-red-800/20 border border-red-500/30 rounded-lg p-4">
                  <p className="text-gray-300 text-sm mb-1">Tổng vũ khí</p>
                  <p className="text-3xl font-bold text-white">{realtimeStats.totalWeapons}</p>
                </div>

                <div className="bg-gradient-to-r from-yellow-600/20 to-yellow-800/20 border border-yellow-500/30 rounded-lg p-4">
                  <p className="text-gray-300 text-sm mb-1">Người cầm vũ khí</p>
                  <p className="text-3xl font-bold text-white">{realtimeStats.withPerson}</p>
                </div>

                <div className="bg-gradient-to-r from-blue-600/20 to-blue-800/20 border border-blue-500/30 rounded-lg p-4">
                  <p className="text-gray-300 text-sm mb-1">FPS</p>
                  <p className="text-3xl font-bold text-white">{realtimeStats.fps}</p>
                </div>
              </div>
            </div>

            <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4">
              <h4 className="text-blue-400 font-semibold mb-2">💡 Hướng dẫn</h4>
              <ul className="text-gray-300 text-sm space-y-1">
                <li>• Cho phép truy cập webcam</li>
                <li>• Nhấn Start để bắt đầu</li>
                <li>• Hệ thống tự động phát hiện</li>
                <li>• Xem kết quả realtime</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Video Mode */}
      {mode === 'video' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Video Display with Real-time Detection */}
          <div className="lg:col-span-2 bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-white">Phát hiện Video Real-time</h2>
              <div className="flex items-center gap-2">
                {isStreaming ? (
                  <Wifi className="w-5 h-5 text-green-400 animate-pulse" />
                ) : (
                  <WifiOff className="w-5 h-5 text-gray-500" />
                )}
                <span className={`text-sm ${isStreaming ? 'text-green-400' : 'text-gray-500'}`}>
                  {isStreaming ? 'Đang xử lý' : 'Chưa xử lý'}
                </span>
              </div>
            </div>

            {/* Video Display Area */}
            <div className="relative bg-black rounded-lg overflow-hidden mb-4" style={{ minHeight: '400px' }}>
              {!videoPreview ? (
                <div
                  onClick={() => videoInputRef.current?.click()}
                  className="absolute inset-0 border-2 border-dashed border-slate-600 rounded-xl flex items-center justify-center hover:border-blue-500 hover:bg-slate-700/30 transition cursor-pointer"
                >
                  <div className="text-center">
                    <Video className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                    <p className="text-gray-300 mb-2">Click để chọn video</p>
                    <p className="text-gray-500 text-sm">Hỗ trợ: MP4, AVI, MOV, MKV</p>
                  </div>
                  <input
                    ref={videoInputRef}
                    type="file"
                    accept="video/*"
                    onChange={handleVideoSelect}
                    className="hidden"
                  />
                </div>
              ) : (
                <>
                  {/* Original video (for playback) */}
                  <video
                    ref={videoPlaybackRef}
                    src={videoPreview}
                    className="w-full h-auto max-h-[480px] object-contain"
                    onLoadedMetadata={(e) => {
                      // Setup canvas when video is loaded
                      if (canvasRef.current) {
                        const video = e.target;
                        const canvas = canvasRef.current;
                        canvas.width = video.videoWidth;
                        canvas.height = video.videoHeight;
                        
                        // Start render loop
                        startRenderLoop(video, canvas);
                      }
                    }}
                    style={{ display: isStreaming ? 'none' : 'block' }}
                  />
                  
                  {/* Canvas overlay for real-time detection boxes */}
                  <canvas
                    ref={canvasRef}
                    className="w-full h-auto max-h-[480px] object-contain"
                    style={{ display: isStreaming ? 'block' : 'none' }}
                  />
                  
                  {/* Reset button */}
                  <button
                    onClick={handleVideoReset}
                    className="absolute top-2 right-2 bg-red-600 hover:bg-red-700 text-white p-2 rounded-full transition z-10"
                    title="Xóa video"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </>
              )}
            </div>

            {/* Video Info (when video is loaded) */}
            {videoFile && (
              <div className="bg-slate-700/50 rounded-lg p-4 mb-4">
                <h3 className="text-white font-semibold mb-2">📁 Thông tin video</h3>
                <div className="grid grid-cols-2 gap-2 text-sm text-gray-300">
                  <p>Tên: {videoFile?.name}</p>
                  <p>Kích thước: {(videoFile?.size / 1024 / 1024).toFixed(2)} MB</p>
                  <p>Loại: {videoFile?.type}</p>
                </div>
              </div>
            )}

            {/* Control Buttons */}
            {videoPreview && (
              <div className="flex gap-3">
                {!isStreaming ? (
                  <button
                    onClick={startStreaming}
                    className="flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition flex items-center justify-center gap-2"
                  >
                    <Play className="w-5 h-5" />
                    Bắt đầu phát hiện
                  </button>
                ) : (
                  <button
                    onClick={stopStreaming}
                    className="flex-1 bg-red-600 hover:bg-red-700 text-white font-semibold py-3 px-6 rounded-lg transition flex items-center justify-center gap-2"
                  >
                    <Square className="w-5 h-5" />
                    Dừng lại
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Realtime Stats */}
          <div className="space-y-4">
            <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Thống kê Real-time</h3>
              
              <div className="space-y-4">
                <div className="bg-gradient-to-r from-red-600/20 to-red-800/20 border border-red-500/30 rounded-lg p-4">
                  <p className="text-gray-300 text-sm mb-1">Tổng vũ khí</p>
                  <p className="text-3xl font-bold text-white">{realtimeStats.totalWeapons}</p>
                </div>

                <div className="bg-gradient-to-r from-yellow-600/20 to-yellow-800/20 border border-yellow-500/30 rounded-lg p-4">
                  <p className="text-gray-300 text-sm mb-1">Người cầm vũ khí</p>
                  <p className="text-3xl font-bold text-white">{realtimeStats.withPerson}</p>
                </div>

                <div className="bg-gradient-to-r from-blue-600/20 to-blue-800/20 border border-blue-500/30 rounded-lg p-4">
                  <p className="text-gray-300 text-sm mb-1">FPS</p>
                  <p className="text-3xl font-bold text-white">{realtimeStats.fps}</p>
                </div>
              </div>
            </div>

            <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4">
              <h4 className="text-blue-400 font-semibold mb-2">💡 Hướng dẫn</h4>
              <ul className="text-gray-300 text-sm space-y-1">
                <li>• Chọn video để xử lý</li>
                <li>• Nhấn "Bắt đầu" để phát hiện real-time</li>
                <li>• Video được xử lý trên máy client</li>
                <li>• Không upload lên server</li>
                <li>• Kết quả hiển thị ngay lập tức</li>
              </ul>
            </div>

            <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4">
              <h4 className="text-green-400 font-semibold mb-2">✨ Ưu điểm</h4>
              <ul className="text-gray-300 text-sm space-y-1">
                <li>• ⚡ Không bị timeout</li>
                <li>• 🔒 Dữ liệu không rời máy</li>
                <li>• 🎯 Phát hiện real-time</li>
                <li>• 💾 Tiết kiệm băng thông</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
