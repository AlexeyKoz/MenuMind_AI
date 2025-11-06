import React from 'react';
import { Lock, Mail, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface LockedFeatureProps {
  featureName: string;
  description: string;
  benefits: string[];
}

export const LockedFeature: React.FC<LockedFeatureProps> = ({
  featureName, description, benefits
}) => {
  const navigate = useNavigate();
  
  return (
    <div className="flex items-center justify-center min-h-[60vh] p-8">
      <div className="max-w-2xl w-full">
        <div className="flex justify-center mb-6">
          <div className="bg-gradient-to-br from-indigo-100 to-purple-100 rounded-full p-6">
            <Lock className="w-16 h-16 text-indigo-600" />
          </div>
        </div>
        
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold mb-3">{featureName} is Locked</h2>
          <p className="text-lg text-gray-600">{description}</p>
        </div>
        
        <div className="bg-white rounded-lg shadow-lg border-2 border-indigo-100 p-6 mb-8">
          <h3 className="text-xl font-semibold mb-4">Unlock by Verifying Your Email</h3>
          <ul className="space-y-3">
            {benefits.map((benefit, i) => (
              <li key={i} className="flex items-start gap-3">
                <div className="bg-green-100 rounded-full p-1 mt-0.5">
                  <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span>{benefit}</span>
              </li>
            ))}
          </ul>
        </div>
        
        <button
          onClick={() => navigate('/verify-email')}
          className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-4 px-6 rounded-lg font-semibold text-lg hover:from-indigo-700 hover:to-purple-700 flex items-center justify-center gap-2"
        >
          <Mail className="w-6 h-6" />
          Verify Email Now
          <ArrowRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

