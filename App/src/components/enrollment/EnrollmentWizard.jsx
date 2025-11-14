import { Check } from 'lucide-react';
import { clsx } from 'clsx';

const EnrollmentWizard = ({ currentStep, steps, onStepClick }) => {
  return (
    <nav aria-label="Progress" className="mb-8">
      <ol className="space-y-4 md:flex md:space-y-0 md:space-x-8">
        {steps.map((step, index) => {
          const stepNumber = index + 1;
          const isCompleted = currentStep > stepNumber;
          const isCurrent = currentStep === stepNumber;
          const isUpcoming = currentStep < stepNumber;

          return (
            <li key={step.id} className="md:flex-1">
              <div
                className={clsx(
                  'group flex flex-col border-l-4 py-2 pl-4 md:border-l-0 md:border-t-4 md:pl-0 md:pt-4 md:pb-0',
                  {
                    'border-blue-600': isCurrent,
                    'border-green-600': isCompleted,
                    'border-gray-200': isUpcoming,
                  }
                )}
              >
                <button
                  onClick={() => onStepClick && onStepClick(stepNumber)}
                  className={clsx(
                    'flex items-center text-left',
                    {
                      'cursor-pointer hover:text-gray-900': onStepClick && !isUpcoming,
                      'cursor-default': !onStepClick || isUpcoming,
                    }
                  )}
                  disabled={isUpcoming && !onStepClick}
                >
                  <span className="flex-shrink-0">
                    <span
                      className={clsx(
                        'w-10 h-10 flex items-center justify-center rounded-full text-sm font-medium',
                        {
                          'bg-blue-600 text-white': isCurrent,
                          'bg-green-600 text-white': isCompleted,
                          'bg-gray-200 text-gray-600': isUpcoming,
                        }
                      )}
                    >
                      {isCompleted ? (
                        <Check className="w-6 h-6" />
                      ) : (
                        stepNumber
                      )}
                    </span>
                  </span>
                  <span className="ml-4 min-w-0 flex flex-col">
                    <span
                      className={clsx('text-sm font-medium', {
                        'text-blue-600': isCurrent,
                        'text-green-600': isCompleted,
                        'text-gray-500': isUpcoming,
                      })}
                    >
                      {step.name}
                    </span>
                    <span className="text-sm text-gray-500">{step.description}</span>
                  </span>
                </button>
              </div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
};

export default EnrollmentWizard;