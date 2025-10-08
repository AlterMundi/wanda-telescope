(function () {
  const root = document.documentElement;

  const qs = (selector, scope = document) => scope.querySelector(selector);
  const qsa = (selector, scope = document) => Array.from(scope.querySelectorAll(selector));

  const setAttr = (el, attr, value) => {
    if (!el) return;
    if (value === false || value === null || value === undefined) {
      el.removeAttribute(attr);
    } else {
      el.setAttribute(attr, value === true ? "" : value);
    }
  };

  function initTabs() {
    const tabButtons = qsa(".ui-tab-button");
    const tabPanels = qsa(".ui-tab-content");

    tabButtons.forEach((button) => {
      button.addEventListener("click", () => {
        const targetId = button.getAttribute("data-tab-target");

        tabButtons.forEach((btn) => btn.classList.remove("active"));
        tabPanels.forEach((panel) => {
          if (panel.id === `tab-${targetId}`) {
            panel.removeAttribute("hidden");
          } else {
            setAttr(panel, "hidden", "hidden");
          }
        });

        button.classList.add("active");
      });
    });
  }

  function initCollapsibles() {
    qsa("[data-collapsible]").forEach((section) => {
      const trigger = qs("[data-collapsible-trigger]", section);
      const content = qs("[data-collapsible-content]", section);
      if (!trigger || !content) return;

      let open = section.hasAttribute("data-open") || section.dataset.open === "true";
      if (!open) {
        setAttr(content, "hidden", "hidden");
      }

      trigger.addEventListener("click", () => {
        open = !open;
        if (open) {
          content.removeAttribute("hidden");
        } else {
          setAttr(content, "hidden", "hidden");
        }
        trigger.classList.toggle("open", open);
      });
    });
  }

  function initCameraControls() {
    const container = qs('[data-component="camera"]');
    if (!container) return;

    const exposureSlider = qs('[data-role="exposure-slider"]', container);
    const exposureDisplay = qs('[data-bind="exposure-display"]', container);
    const isoSlider = qs('[data-role="iso-slider"]', container);
    const isoDisplay = qs('[data-bind="iso-display"]', container);
    const nightVisionToggle = qs('[data-role="night-vision-toggle"]', container);
    const nightVisionField = qs('[data-night-vision-intensity]', container);
    const nightVisionDisplay = qs('[data-bind="night-vision-display"]', container);
    const nightVisionInput = qs('#night-vision-intensity', container);
    const performanceSlider = qs('[data-role="performance-slider"]', container);
    const performanceDisplay = qs('[data-bind="performance-display"]', container);

    if (exposureSlider && exposureDisplay) {
      exposureSlider.addEventListener("input", () => {
        const value = Number(exposureSlider.value);
        const seconds = sliderToSeconds(value);
        exposureDisplay.textContent = formatSeconds(seconds);
      });

      qsa('[data-preset]', container).forEach((button) => {
        const preset = Number(button.getAttribute("data-preset"));
        button.addEventListener("click", () => {
          const sliderValue = secondsToSlider(preset);
          exposureSlider.value = sliderValue;
          exposureSlider.dispatchEvent(new Event("input"));
        });
      });
    }

    if (isoSlider && isoDisplay) {
      isoSlider.addEventListener("input", () => {
        const sliderValue = Number(isoSlider.value);
        isoDisplay.textContent = isoSliderLabel(sliderValue);
      });
    }

    if (nightVisionToggle && nightVisionField) {
      const updateNightVisionState = () => {
        const enabled = nightVisionToggle.checked;
        nightVisionField.toggleAttribute("data-enabled", enabled);
        if (nightVisionInput) {
          nightVisionInput.disabled = !enabled;
        }
      };

      nightVisionToggle.addEventListener("change", updateNightVisionState);
      updateNightVisionState();
    }

    if (nightVisionInput && nightVisionDisplay) {
      nightVisionInput.addEventListener("input", () => {
        nightVisionDisplay.textContent = nightVisionInput.value;
      });

      qsa('[data-night-vision-preset]', container).forEach((button) => {
        button.addEventListener("click", () => {
          const preset = button.getAttribute("data-night-vision-preset");
          nightVisionInput.value = preset;
          nightVisionInput.dispatchEvent(new Event("input"));
        });
      });
    }

    if (performanceSlider && performanceDisplay) {
      performanceSlider.addEventListener("input", () => {
        performanceDisplay.textContent = performanceLabel(Number(performanceSlider.value));
      });
    }
  }

  function sliderToSeconds(value) {
    const minSeconds = 0.1;
    const maxSeconds = 230;
    const logRange = Math.log(maxSeconds / minSeconds);
    return minSeconds * Math.exp((value * logRange) / 1000);
  }

  function secondsToSlider(seconds) {
    const minSeconds = 0.1;
    const maxSeconds = 230;
    const logRange = Math.log(maxSeconds / minSeconds);
    return Math.round((Math.log(seconds / minSeconds) / logRange) * 1000);
  }

  function formatSeconds(seconds) {
    if (seconds < 1) {
      return `${seconds.toFixed(1)}s`;
    }
    if (seconds < 10) {
      return `${seconds.toFixed(1)}s`;
    }
    return `${Math.round(seconds)}s`;
  }

  function isoSliderLabel(value) {
    const minIso = 100;
    const maxIso = 1600;
    const iso = minIso + ((maxIso - minIso) * value) / 1000;
    if (Math.abs(iso - 100) <= 50) return "Low (100)";
    if (Math.abs(iso - 800) <= 50) return "Medium (800)";
    if (Math.abs(iso - 1600) <= 50) return "High (1600)";
    return `${Math.round(iso)}`;
  }

  function performanceLabel(value) {
    const labels = [
      "High Quality",
      "Good Quality",
      "Balanced",
      "Moderate",
      "Low CPU",
      "Lowest CPU",
    ];
    return labels[Math.max(0, Math.min(labels.length - 1, value))];
  }

  function initMountControls() {
    const container = qs('[data-component="mount"]');
    if (!container) return;

    const speedSlider = qs('[data-role="mount-speed-slider"]', container);
    const speedDisplay = qs('[data-bind="mount-speed-display"]', container);
    if (speedSlider && speedDisplay) {
      speedSlider.addEventListener("input", () => {
        speedDisplay.textContent = `${Number(speedSlider.value).toFixed(1)}`;
      });
    }
  }

  function initSessionControls() {
    const sessionForm = qs('#session-form');
    const stopForm = qs('#stop-session-form');
    const progressSection = qs('[data-session-progress]');
    const sessionStatus = qs('[data-session-status-message]');
    const badge = qs('[data-session-state]');
    const progressFill = qs('#progress-fill');
    const progressText = qs('#progress-text');
    const sessionName = qs('[data-session-name]');
    const sessionCount = qs('[data-session-count]');
    const sessionTime = qs('[data-session-time]');
    const sessionTimeInfo = qs('[data-session-time-info]');

    if (!sessionForm) return;

    sessionForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const formData = new FormData(sessionForm);
      fetch(sessionForm.action, {
        method: "POST",
        body: formData,
        headers: {
          Accept: "application/json",
        },
      })
        .then((response) => response.json())
        .then((data) => {
          if (!data.success) {
            updateSessionStatus(`Session failed to start: ${data.error ?? "Unknown error"}`, "error");
            return;
          }
          sessionForm.classList.add("ui-hidden");
          stopForm?.classList.remove("ui-hidden");
          progressSection?.classList.remove("ui-hidden");
          updateSessionStatus("Session running", "active");
          badge && (badge.textContent = "Active");
        })
        .catch((error) => {
          console.error("Failed to start session", error);
          updateSessionStatus("Failed to start session", "error");
        });
    });

    stopForm?.addEventListener("submit", (event) => {
      event.preventDefault();
      fetch(stopForm.action, {
        method: "POST",
        headers: {
          Accept: "application/json",
        },
      })
        .then((response) => response.json())
        .then((data) => {
          if (!data.success) {
            updateSessionStatus(`Failed to stop session: ${data.error ?? "Unknown error"}`, "error");
            return;
          }
          resetSessionUI();
          updateSessionStatus("Session stopped", "inactive");
        })
        .catch((error) => {
          console.error("Failed to stop session", error);
          updateSessionStatus("Failed to stop session", "error");
        });
    });

    function updateSessionStatus(message, status) {
      if (sessionStatus) {
        sessionStatus.textContent = message;
        sessionStatus.dataset.status = status;
      }
    }

    function resetSessionUI() {
      sessionForm?.classList.remove("ui-hidden");
      stopForm?.classList.add("ui-hidden");
      progressSection?.classList.add("ui-hidden");
      badge && (badge.textContent = "Idle");
      if (progressFill) progressFill.style.width = "0%";
      if (progressText) progressText.textContent = "0%";
      if (sessionName) sessionName.textContent = "-";
      if (sessionCount) sessionCount.textContent = "0 / 0";
      if (sessionTime) sessionTime.textContent = "0s";
      sessionTimeInfo?.classList.add("ui-hidden");
    }

    const sessionStatusEndpoint = "/session_status";
    let sessionPollTimer = null;

    function pollSessionStatus() {
      clearTimeout(sessionPollTimer);
      fetch(sessionStatusEndpoint, {
        headers: {
          Accept: "application/json",
        },
      })
        .then((response) => response.json())
        .then((data) => {
          if (!data.session_status) {
            sessionPollTimer = setTimeout(pollSessionStatus, 5000);
            return;
          }

          const status = data.session_status;
          const statusTextEl = qs('[data-session-status]');
          if (statusTextEl) {
            statusTextEl.textContent = status.state === "running" ? "Running" : "Idle";
          }
          if (progressSection && status.state === "running") {
            const pct = Math.round(status.progress_percent ?? 0);
            if (progressFill) progressFill.style.width = `${pct}%`;
            if (progressText) progressText.textContent = `${pct}%`;
            if (sessionName) sessionName.textContent = status.name ?? "-";
            if (sessionCount) {
              const total = status.total_images ?? 0;
              const captured = status.captured_images ?? 0;
              sessionCount.textContent = `${captured} / ${total}`;
            }
            if (sessionTime) sessionTime.textContent = formatDuration(status.elapsed_seconds ?? 0);
            if (status.remaining_seconds !== undefined && sessionTimeInfo) {
              sessionTimeInfo.classList.remove("ui-hidden");
              sessionTimeInfo.textContent = `ETA ${formatDuration(status.remaining_seconds)}`;
            }
            updateSessionStatus("Session running", "active");
            badge && (badge.textContent = "Active");
          } else if (status.state === "idle") {
            resetSessionUI();
            updateSessionStatus("Ready to start session", "inactive");
          }
        })
        .catch((error) => {
          console.error("Failed to load session status", error);
        })
        .finally(() => {
          sessionPollTimer = setTimeout(pollSessionStatus, 5000);
        });
    }

    pollSessionStatus();
  }

  function formatDuration(seconds) {
    seconds = Math.max(0, Math.floor(seconds));
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) {
      return `${h}h ${m}m ${s}s`;
    }
    if (m > 0) {
      return `${m}m ${s}s`;
    }
    return `${s}s`;
  }

  function initCaptureEvents() {
    const captureForm = qs('#capture-form');
    const captureCountEl = qs('[data-capture-count]');
    const captureGrid = qs('[data-capture-grid]');
    const statusText = qs('[data-capture-status]');
    const proxyButton = qs('[data-action="capture-still-proxy"]');
    const captureSubmitButton = captureForm?.querySelector('button[type="submit"]');
    let count = Number(captureCountEl?.textContent ?? 0);
    let captureInFlight = false;

    if (!captureForm) return;

    const setCaptureDisabled = (disabled) => {
      if (captureSubmitButton) captureSubmitButton.disabled = disabled;
      if (proxyButton) proxyButton.disabled = disabled;
    };

    if (proxyButton) {
      proxyButton.addEventListener("click", () => {
        if (captureInFlight) return;
        captureForm.dispatchEvent(new Event("submit", { cancelable: true }));
      });
    }

    captureForm.addEventListener("submit", (event) => {
      event.preventDefault();
      if (captureInFlight) return;
      captureInFlight = true;
      setCaptureDisabled(true);

      const formData = new FormData(captureForm);
      fetch(captureForm.action, {
        method: "POST",
        headers: {
          Accept: "application/json",
        },
        body: formData,
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error(`Capture request failed with status ${response.status}`);
          }
          return response.json();
        })
        .then((data) => {
          if (data.success) {
            statusText && (statusText.textContent = data.capture_status ?? "Capture complete");
            count += 1;
            if (captureCountEl) captureCountEl.textContent = String(count);
            if (captureGrid) {
              const thumbnail = document.createElement("div");
              thumbnail.className = "ui-thumbnail";
              thumbnail.textContent = `IMG ${count}`;
              captureGrid.prepend(thumbnail);
            }
          } else {
            statusText && (statusText.textContent = data.error ?? "Capture failed");
            throw new Error(data.error || "Capture failed");
          }
        })
        .catch((error) => {
          console.error("Capture request failed", error);
          statusText && (statusText.textContent = "Capture initiated, waiting for camera...");
          setCaptureDisabled(false);
          captureInFlight = false;
          captureForm.submit();
        })
        .finally(() => {
          if (captureInFlight) {
            captureInFlight = false;
            setCaptureDisabled(false);
          }
        });
    });

    const startVideoForm = qs('#start-video-form');
    const stopVideoForm = qs('#stop-video-form');
    let videoInFlight = false;

    const submitVideoForm = (form) => {
      if (!form || videoInFlight) return;
      videoInFlight = true;
      const submitButton = form.querySelector('button[type="submit"]');
      if (submitButton) submitButton.disabled = true;

      fetch(form.action, {
        method: "POST",
        headers: {
          Accept: "application/json",
        },
        body: new FormData(form),
      })
        .catch((error) => {
          console.error("Video request failed", error);
          form.submit();
        })
        .finally(() => {
          videoInFlight = false;
          if (submitButton) submitButton.disabled = false;
        });
    };

    [startVideoForm, stopVideoForm].forEach((form) => {
      if (!form) return;
      form.addEventListener("submit", (event) => {
        event.preventDefault();
        submitVideoForm(form);
      });
    });
  }

  function initFullscreenToggle() {
    const toggle = qs('[data-action="toggle-fullscreen"]');
    if (!toggle) return;

    toggle.addEventListener("click", () => {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch((error) => {
          console.warn("Fullscreen request failed", error);
        });
      } else {
        document.exitFullscreen().catch(() => {});
      }
    });
  }

  function initOverlays() {
    const viewport = qs(".ui-viewport__display");
    if (!viewport) return;

    const histogramToggle = qs('[data-toggle="histogram"]');
    const focusToggle = qs('[data-toggle="focus-assist"]');
    const histogramOverlay = qs('.ui-overlay--histogram', viewport);
    const focusOverlay = qs('.ui-overlay--focus', viewport);

    histogramToggle?.addEventListener("click", () => {
      const hidden = histogramOverlay?.hasAttribute("hidden");
      if (hidden) {
        histogramOverlay?.removeAttribute("hidden");
        viewport.dataset.showHistogram = "true";
      } else {
        histogramOverlay && setAttr(histogramOverlay, "hidden", "hidden");
        viewport.dataset.showHistogram = "false";
      }
    });

    focusToggle?.addEventListener("click", () => {
      const hidden = focusOverlay?.hasAttribute("hidden");
      if (hidden) {
        focusOverlay?.removeAttribute("hidden");
        viewport.dataset.showFocusAssist = "true";
      } else {
        focusOverlay && setAttr(focusOverlay, "hidden", "hidden");
        viewport.dataset.showFocusAssist = "false";
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initCollapsibles();
    initCameraControls();
    initMountControls();
    initSessionControls();
    initCaptureEvents();
    initFullscreenToggle();
    initOverlays();
  });
})();
