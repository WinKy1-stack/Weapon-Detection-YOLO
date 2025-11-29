import { useState, useRef, useEffect } from 'react';
import { Upload, Camera, AlertTriangle, CheckCircle, X, Loader2, Image as ImageIcon, Video, Wifi, WifiOff } from 'lucide-react';
import { detectionAPI } from '../services/api';
import toast from 'react-hot-toast';

export default function Detection() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [resultImage, setResultImage] = useState('');
  const fileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        toast.error('Vui lòng chọn file hình ảnh');
        return;
      }
      
      setSelectedFile(file);
      setResult(null);
      setResultImage('');
      
      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDetect = async () => {
    if (!selectedFile) {
      toast.error('Vui lòng chọn hình ảnh');
      return;
    }

    setLoading(true);
    try {
      const response = await detectionAPI.detectWeapon(selectedFile);
      setResult(response);
      
      if (response.result_image_base64) {
        setResultImage(`data:image/jpeg;base64,${response.result_image_base64}`);
      }
      
      if (response.detections && response.detections.length > 0) {
        toast.success(`Phát hiện ${response.detections.length} vũ khí!`);
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

  const handleReset = () => {
    setSelectedFile(null);
    setPreview('');
    setResult(null);
    setResultImage('');
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
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
          <Camera className="w-8 h-8 text-blue-400" />
          Phát hiện vũ khí
        </h1>
        <p className="text-gray-400">
          Upload hình ảnh để phát hiện vũ khí bằng AI
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload Section */}
        <div className="space-y-6">
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <Upload className="w-5 h-5 text-blue-400" />
              Tải ảnh lên
            </h2>

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
                  <img
                    src={preview}
                    alt="Preview"
                    className="w-full h-auto"
                  />
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
                  
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="bg-slate-700 hover:bg-slate-600 text-white font-semibold py-3 px-6 rounded-lg transition"
                  >
                    Chọn ảnh khác
                  </button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Instructions */}
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-blue-400 mb-3">💡 Hướng dẫn</h3>
            <ul className="space-y-2 text-gray-300 text-sm">
              <li>• Chọn hình ảnh chứa vũ khí cần phát hiện</li>
              <li>• Ảnh nên rõ nét và có đủ ánh sáng</li>
              <li>• Hệ thống sẽ tự động đánh dấu vị trí vũ khí</li>
              <li>• Kết quả bao gồm độ tin cậy và mức độ nguy hiểm</li>
            </ul>
          </div>
        </div>

        {/* Results Section */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
          <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-400" />
            Kết quả phát hiện
          </h2>

          {!result ? (
            <div className="text-center py-16">
              <Camera className="w-20 h-20 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400 text-lg">Chưa có kết quả</p>
              <p className="text-gray-500 text-sm mt-2">Upload và phát hiện ảnh để xem kết quả</p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Result Image */}
              {resultImage && (
                <div className="rounded-xl overflow-hidden border border-slate-600">
                  <img
                    src={resultImage}
                    alt="Detection Result"
                    className="w-full h-auto"
                  />
                </div>
              )}

              {/* Detection Summary */}
              <div className="bg-slate-700/30 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-gray-400">Số lượng phát hiện:</span>
                  <span className="text-2xl font-bold text-white">
                    {result.detections?.length || 0}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Model:</span>
                  <span className="text-white font-semibold">{result.model}</span>
                </div>
              </div>

              {/* Detections List */}
              {result.detections && result.detections.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold text-white">Chi tiết:</h3>
                  {result.detections.map((detection, index) => (
                    <div
                      key={index}
                      className={`border rounded-lg p-4 ${getDangerColor(detection.danger_level)}`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <p className="font-semibold text-lg">
                            {detection.class_name || 'Unknown'}
                          </p>
                          <p className="text-sm opacity-90">
                            {getDangerLabel(detection.danger_level)}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-2xl font-bold">
                            {(detection.confidence * 100).toFixed(1)}%
                          </p>
                          <p className="text-xs opacity-75">Độ tin cậy</p>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-2 text-sm mt-3 opacity-75">
                        <div>
                          <span className="block">Vị trí X:</span>
                          <span className="font-mono">{detection.bbox[0].toFixed(0)}</span>
                        </div>
                        <div>
                          <span className="block">Vị trí Y:</span>
                          <span className="font-mono">{detection.bbox[1].toFixed(0)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {result.detections?.length === 0 && (
                <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-6 text-center">
                  <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-3" />
                  <p className="text-green-400 font-semibold text-lg">An toàn</p>
                  <p className="text-green-300/70 text-sm mt-1">
                    Không phát hiện vũ khí trong ảnh
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
