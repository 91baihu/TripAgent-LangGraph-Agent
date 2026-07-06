/** 行程地图视图 — 集成高德地图 */

import { useParams, useNavigate } from "react-router-dom";
import { Button } from "../../components/Button/Button";

export function MapView() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  return (
    <div className="flex flex-col h-dvh bg-surface-page">
      {/* 顶栏 */}
      <header
        className="
          flex-shrink-0 h-14 bg-surface-card border-b border-divider
          flex items-center gap-3 px-4
        "
      >
        <button
          onClick={() => navigate(-1)}
          className="w-8 h-8 flex items-center justify-center text-text-secondary hover:text-text-primary"
        >
          ←
        </button>
        <h1 className="text-h2 text-text-primary flex-1">行程地图</h1>
      </header>

      {/* 地图区域 */}
      <div className="flex-1 bg-surface-input flex items-center justify-center">
        <div className="text-center p-6">
          <span className="text-5xl mb-4 block">🗺️</span>
          <p className="text-h3 text-text-primary mb-2">地图加载中</p>
          <p className="text-body text-text-secondary mb-4">
            集成高德 JS API 2.0 后可展示：
          </p>
          <ul className="text-left text-caption text-text-secondary space-y-1 mb-6">
            <li>· 景点 Marker 标注（编号 1→2→3）</li>
            <li>· 蓝色虚线路线</li>
            <li>· 天气浮层（右上角）</li>
            <li>· 交通方式标记（🚇/🚶/🚗）</li>
          </ul>
          <Button onClick={() => navigate(`/trips/${id}`)} variant="secondary">
            返回行程详情
          </Button>
        </div>
      </div>
    </div>
  );
}
