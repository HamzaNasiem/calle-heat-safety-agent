import { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallbackTitle?: string
}

interface State {
  hasError: boolean
  error: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error caught by ErrorBoundary:', error, errorInfo)
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 font-sans text-xs space-y-2 m-2">
          <div className="flex items-center justify-between">
            <span className="font-bold uppercase tracking-wider text-rose-900 flex items-center gap-1.5">
              <span>⚠️</span> {this.props.fallbackTitle || 'Component Error'}
            </span>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="px-2.5 py-1 bg-rose-600 hover:bg-rose-700 rounded-lg text-xs font-semibold text-white transition-colors"
            >
              Retry
            </button>
          </div>
          <p className="text-[11px] text-rose-700/90 font-medium">
            {this.state.error?.message || 'An unexpected error occurred.'}
          </p>
        </div>
      )
    }

    return this.props.children
  }
}
