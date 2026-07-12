/** 全局错误边界 — 捕获渲染异常，避免白屏 */

import { Component, type ReactNode } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="flex flex-col items-center justify-center min-h-dvh px-6 bg-surface-page text-center">
          <div className="w-16 h-16 rounded-full bg-semantic-error/10 flex items-center justify-center mb-4">
            <span className="text-3xl">⚠️</span>
          </div>
          <h2 className="text-h2 text-text-primary mb-2">页面出错了</h2>
          <p className="text-body text-text-secondary mb-4 max-w-[300px]">
            {this.state.error?.message || "发生了未知错误"}
          </p>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.href = "/";
            }}
            className="px-6 py-2 bg-ink text-white rounded-button hover:bg-ink-secondary active:scale-[0.97] transition-all"
          >
            返回首页
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
