import { Moon, Sun, Server, Github } from 'lucide-react'
import { Chip } from './ui'
import { cx } from '../lib/format'

export function Header({
  theme,
  onToggleTheme,
  backend,
  backendLoading,
}: {
  theme: 'dark' | 'light'
  onToggleTheme: () => void
  backend?: string
  backendLoading: boolean
}) {
  return (
    <header className="sticky top-0 z-30 border-b border-zinc-200/70 bg-zinc-50/80 backdrop-blur-lg dark:border-zinc-800/70 dark:bg-zinc-950/70">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-brand-400 to-brand-600 text-xl shadow-[0_8px_24px_-10px_rgba(16,185,129,0.8)]">
            <span aria-hidden>🪶</span>
          </div>
          <div className="leading-tight">
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
                GraphThrift
              </h1>
              <span className="hidden rounded-md bg-zinc-500/10 px-1.5 py-0.5 font-mono text-[10px] uppercase tracking-wider text-zinc-500 dark:text-zinc-400 sm:inline">
                OSS
              </span>
            </div>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              Cut LLM cost — proven safe
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <div className="hidden sm:block">
            {backendLoading ? (
              <Chip tone="neutral">
                <Server className="h-3 w-3" />
                connecting…
              </Chip>
            ) : backend ? (
              <span
                title={
                  backend === 'fake'
                    ? 'Live demo runs on a deterministic simulator (no API keys). The optimizers & eval gate are real code; validated separately on real models + Neo4j.'
                    : `Backend: ${backend}`
                }
              >
                <Chip tone={backend === 'fake' ? 'neutral' : 'accent'}>
                  <Server className="h-3 w-3" />
                  {backend === 'fake' ? 'simulated demo' : backend}
                </Chip>
              </span>
            ) : (
              <Chip tone="bad">
                <Server className="h-3 w-3" />
                offline
              </Chip>
            )}
          </div>

          <a
            href="https://github.com/sarcascoder/graphthrift"
            target="_blank"
            rel="noreferrer"
            className="grid h-9 w-9 place-items-center rounded-xl border border-zinc-200 bg-white text-zinc-600 transition hover:bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-800/60 dark:text-zinc-300 dark:hover:bg-zinc-800"
            aria-label="GitHub repository"
          >
            <Github className="h-4 w-4" />
          </a>

          <button
            onClick={onToggleTheme}
            aria-label="Toggle color theme"
            className="grid h-9 w-9 place-items-center rounded-xl border border-zinc-200 bg-white text-zinc-600 transition hover:bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-800/60 dark:text-zinc-300 dark:hover:bg-zinc-800"
          >
            <Sun className={cx('h-4 w-4', theme === 'dark' ? 'hidden' : 'block')} />
            <Moon className={cx('h-4 w-4', theme === 'dark' ? 'block' : 'hidden')} />
          </button>
        </div>
      </div>
    </header>
  )
}
