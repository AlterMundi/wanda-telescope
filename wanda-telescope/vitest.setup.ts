import "@testing-library/jest-dom/vitest"

class MockIntersectionObserver {
  root: Element | Document | null
  rootMargin: string
  thresholds: ReadonlyArray<number>

  constructor(callback: IntersectionObserverCallback, options: IntersectionObserverInit = {}) {
    this.root = options.root ?? null
    this.rootMargin = options.rootMargin ?? "0px"
    this.thresholds = Array.isArray(options.threshold)
      ? options.threshold
      : [options.threshold ?? 0]

    // Immediately invoke the callback with empty entries to simulate setup
    callback([], this as unknown as IntersectionObserver)
  }

  observe() {
    // noop
  }

  unobserve() {
    // noop
  }

  disconnect() {
    // noop
  }

  takeRecords(): IntersectionObserverEntry[] {
    return []
  }
}

Object.defineProperty(window, "IntersectionObserver", {
  writable: true,
  configurable: true,
  value: MockIntersectionObserver,
})

Object.defineProperty(globalThis, "IntersectionObserver", {
  writable: true,
  configurable: true,
  value: MockIntersectionObserver,
})

