import Layout from "@/components/Layout";
import { Target, ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";
import { useState } from "react";

const RedTeam = () => {
  const [attackChecked, setAttackChecked] = useState(false);
  const handleInitiate = () => {
    alert("Attack initiated!");
  };
  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        {/* Back Button */}
        <Link 
          to="/dashboard" 
          className="inline-flex items-center text-cyber-green hover:text-cyber-green-bright mb-8"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Dashboard
        </Link>

        {/* Header */}
        <div className="flex items-center mb-8">
          <Target className="w-8 h-8 mr-4 text-red-500" />
          <h1 className="text-4xl font-bold text-red-500">Red Team</h1>
        </div>

        {/* Attack Option */}
        <div className="flex flex-col items-center py-8">
          <label className="flex items-center space-x-2 mb-4">
            <input
              type="checkbox"
              checked={attackChecked}
              onChange={e => setAttackChecked(e.target.checked)}
              className="form-checkbox h-5 w-5 text-red-600"
            />
            <span className="text-lg">Simulate Phishing Attack</span>
          </label>
          <button
            className={`px-6 py-2 rounded bg-red-500 text-white font-bold transition-colors duration-200 ${attackChecked ? "hover:bg-red-600" : "opacity-50 cursor-not-allowed"}`}
            disabled={!attackChecked}
            onClick={handleInitiate}
          >
            Initiate
          </button>
        </div>

        {/* Content placeholder */}
        <div className="text-center py-8">
          <p className="text-muted-foreground text-lg">
            Red Team assessment tools and reports will be available here.
          </p>
        </div>
      </div>
    </Layout>
  );
};

export default RedTeam;