import React, { useState, useEffect, useRef } from 'react';
import { ChevronDown } from 'lucide-react';


// 自定义下拉选择组件
export const CustomSelect = ({ value, onChange, options, placeholder = "请选择", className = "" }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [selectedOption, setSelectedOption] = useState(null);

    useEffect(() => {
        const option = options.find(opt => opt.value === value);
        setSelectedOption(option);
    }, [value, options]);

    const handleSelect = (option) => {
        onChange(option.value);
        setIsOpen(false);
    };

    return (
        <div className={`relative ${className}`}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full px-4 py-2.5 bg-white/90 backdrop-blur-sm border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent flex items-center justify-between"
            >
                <span className={selectedOption ? 'text-gray-900' : 'text-gray-500'}>
                    {selectedOption ? selectedOption.label : placeholder}
                </span>
                <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${isOpen ? 'transform rotate-180' : ''}`} />
            </button>

            {isOpen && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white/95 backdrop-blur-md border border-gray-200 rounded-xl shadow-lg z-50 overflow-hidden">
                    {options.map((option, index) => (
                        <button
                            key={option.value}
                            onClick={() => handleSelect(option)}
                            className={`w-full px-4 py-2.5 text-left hover:bg-blue-50 transition-colors duration-150 focus:outline-none focus:bg-blue-50 ${value === option.value ? 'bg-blue-50 text-blue-600 font-medium' : 'text-gray-700'
                                } ${index === 0 ? '' : 'border-t border-gray-100'}`}
                        >
                            {option.label}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
};

// 自定义输入框组件
export const CustomInput = ({ placeholder, value, onChange, className = "", ...props }) => (
    <input
        {...props}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        className={`w-full px-4 py-2.5 bg-white/90 backdrop-blur-sm border border-gray-200 rounded-xl shadow-sm hover:shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 ${className}`}
    />
);

// 通用的毛玻璃卡片组件
export const GlassCard = ({ children, className = "" }) => (
    <div className={`bg-white/80 backdrop-blur-md rounded-2xl border border-white/30 shadow-xl p-6 transition-all duration-300 hover:shadow-2xl hover:bg-white/90 ${className}`}>
        {children}
    </div>
);

// 动画按钮组件
export const AnimatedButton = ({ children, onClick, variant = "primary", className = "", disabled = false, size = "default" }) => {
    const sizeClasses = {
        small: "px-3 py-1.5 text-sm",
        default: "px-4 py-2.5",
        large: "px-6 py-3 text-lg"
    };

    const baseClass = `${sizeClasses[size]} rounded-xl font-medium transition-all duration-200 flex items-center gap-2 transform hover:scale-105 active:scale-95 focus:outline-none focus:ring-2 focus:ring-offset-2 shadow-md hover:shadow-lg`;

    const variants = {
        primary: "bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white focus:ring-blue-500",
        secondary: "bg-gradient-to-r from-gray-100 to-gray-200 hover:from-gray-200 hover:to-gray-300 text-gray-700 border border-gray-300 focus:ring-gray-500",
        success: "bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white focus:ring-red-500",
        warning: "bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700 text-white focus:ring-yellow-500",
        danger: "bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white focus:ring-green-500"
    };

    return (
        <button
            onClick={onClick}
            disabled={disabled}
            className={`${baseClass} ${variants[variant]} ${disabled ? 'opacity-50 cursor-not-allowed transform-none' : ''} ${className}`}
        >
            {children}
        </button>
    );
};

// Loading组件
export const LoadingSpinner = () => (
    <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
    </div>
);

// 状态徽章组件
export const StatusBadge = ({ status, type = "default" }) => {
    const configs = {
        task: {
            running: { bg: 'bg-red-100', text: 'text-red-800', label: '运行中' },
            paused: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: '已暂停' },
            stopped: { bg: 'bg-green-100', text: 'text-green-800', label: '已停止' },
            created: { bg: 'bg-blue-100', text: 'text-blue-800', label: '已创建' }
        },
        market: {
            HK: { bg: 'bg-purple-100', text: 'text-purple-800', label: '港股' },
            US: { bg: 'bg-orange-100', text: 'text-orange-800', label: '美股' }
        },
        winRate: {
            high: { bg: 'bg-red-100', text: 'text-red-800' },
            medium: { bg: 'bg-yellow-100', text: 'text-yellow-800' },
            low: { bg: 'bg-green-100', text: 'text-green-800' }
        }
    };

    const getConfig = () => {
        if (type === 'winRate') {
            const rate = parseFloat(status);
            if (rate >= 60) return configs.winRate.high;
            if (rate >= 40) return configs.winRate.medium;
            return configs.winRate.low;
        }
        return configs[type]?.[status] || { bg: 'bg-gray-100', text: 'text-gray-800', label: status };
    };

    const config = getConfig();

    return (
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
            {type === 'winRate' ? `${status}%` : config.label}
        </span>
    );
};

// 数值显示组件
export const ValueDisplay = ({ value, showSign = false, prefix = "¥", className = "" }) => {
    if (typeof value !== 'number' && isNaN(parseFloat(value))) {
        return <span className={`font-bold text-gray-500 ${className}`}>N/A</span>;
    }
    const numValue = typeof value === 'string' ? parseFloat(value) : value;
    const isPositive = numValue > 0;
    const colorClass = isPositive ? 'text-red-600' : 'text-green-600';
    const sign = showSign && isPositive ? '+' : '';

    return (
        <span className={`font-bold ${colorClass} ${className}`}>
            {sign}{prefix}{numValue.toLocaleString()}
        </span>
    );
};