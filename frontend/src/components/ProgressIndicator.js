import React from 'react';
import { ProgressBar } from 'react-bootstrap';

const PIPELINE_STEPS = [
  { key: 'pending', label: 'Pending', pct: 0 },
  { key: 'uploading', label: 'Uploading', pct: 10 },
  { key: 'extracting_audio', label: 'Extracting Audio', pct: 25 },
  { key: 'transcribing', label: 'Transcribing', pct: 40 },
  { key: 'analyzing', label: 'Analyzing', pct: 55 },
  { key: 'generating_edit_plan', label: 'Generating Edit Plan', pct: 70 },
  { key: 'editing', label: 'Editing Video', pct: 85 },
  { key: 'rendering', label: 'Rendering', pct: 95 },
  { key: 'completed', label: 'Completed', pct: 100 },
];

function ProgressIndicator({ status }) {
  const currentStep = PIPELINE_STEPS.find(s => s.key === status);
  const pct = currentStep ? currentStep.pct : 0;
  const isComplete = status === 'completed';
  const isFailed = status === 'failed';

  return (
    <div>
      <div className="d-flex justify-content-between mb-2">
        <span className="text-light fw-bold">
          {isFailed ? 'Pipeline Failed' : currentStep?.label || status}
        </span>
        <span className="text-muted">{pct}%</span>
      </div>

      <ProgressBar
        now={isFailed ? 100 : pct}
        variant={isFailed ? 'danger' : isComplete ? 'success' : 'info'}
        animated={!isComplete && !isFailed}
        striped={!isComplete && !isFailed}
      />

      {/* Step indicators */}
      <div className="d-flex justify-content-between mt-3">
        {PIPELINE_STEPS.filter(s => !['pending'].includes(s.key)).map((step) => {
          const stepIndex = PIPELINE_STEPS.indexOf(step);
          const currentIndex = PIPELINE_STEPS.indexOf(currentStep);
          const isDone = stepIndex <= currentIndex;
          const isCurrent = step.key === status;

          return (
            <div
              key={step.key}
              className="text-center"
              style={{ flex: 1, minWidth: 0 }}
            >
              <div
                className={`step-dot mx-auto mb-1 ${
                  isDone ? 'bg-success' : isCurrent ? 'bg-info' : 'bg-secondary'
                }`}
              />
              <small
                className={`d-none d-lg-block ${
                  isCurrent ? 'text-info fw-bold' : isDone ? 'text-success' : 'text-muted'
                }`}
                style={{ fontSize: '0.7rem' }}
              >
                {step.label}
              </small>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default ProgressIndicator;
