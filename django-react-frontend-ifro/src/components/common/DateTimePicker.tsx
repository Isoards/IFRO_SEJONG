import React, { memo, useCallback, useMemo, useEffect } from "react";
// import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "./Button";

interface DateTimePickerProps {
  currentDate: Date;
  setCurrentDate: (date: Date) => void;
  enableRealTimeUpdate?: boolean;
  updateInterval?: number; // 분 단위 (기본 5분)
  isNowMode?: boolean; // NOW 모드 여부
}

export const DateTimePicker = memo<DateTimePickerProps>(
  ({
    currentDate,
    setCurrentDate,
    enableRealTimeUpdate = false,
    updateInterval = 5,
    isNowMode = false,
  }) => {
    // 실시간 업데이트 로직 (NOW 모드일 때만)
    useEffect(() => {
      if (!enableRealTimeUpdate || !isNowMode) return;

      const interval = setInterval(() => {
        const now = new Date();
        // NOW 모드일 때는 실제 현재 시간을 그대로 설정 (반올림하지 않음)
        setCurrentDate(new Date(now));
      }, 1000); // 1초마다 업데이트

      return () => clearInterval(interval);
    }, [enableRealTimeUpdate, isNowMode, setCurrentDate]);
    const changeDate = useCallback(
      (amount: number) => {
        const newDate = new Date(currentDate);
        newDate.setDate(newDate.getDate() + amount);
        setCurrentDate(newDate);
      },
      [currentDate, setCurrentDate]
    );

    const changeHour = useCallback(
      (amount: number) => {
        const newDate = new Date(currentDate);
        newDate.setHours(newDate.getHours() + amount);
        setCurrentDate(newDate);
      },
      [currentDate, setCurrentDate]
    );

    const changeMinute = useCallback(
      (amount: number) => {
        const newDate = new Date(currentDate);
        let newMinutes = newDate.getMinutes() + amount;
        if (newMinutes < 0) {
          newMinutes = 55;
          newDate.setHours(newDate.getHours() - 1);
        }
        if (newMinutes > 59) {
          newMinutes = 0;
          newDate.setHours(newDate.getHours() + 1);
        }
        newDate.setMinutes(newMinutes);
        setCurrentDate(newDate);
      },
      [currentDate, setCurrentDate]
    );

    const isToday = useMemo(() => {
      const today = new Date();
      return (
        currentDate.getDate() === today.getDate() &&
        currentDate.getMonth() === today.getMonth() &&
        currentDate.getFullYear() === today.getFullYear()
      );
    }, [currentDate]);

    const formatHour = (date: Date) =>
      date.getHours().toString().padStart(2, "0");
    const formatMinute = (date: Date) => {
      const minutes = date.getMinutes();
      if (isNowMode) {
        // NOW 모드일 때는 실제 분을 표시
        return minutes.toString().padStart(2, "0");
      }
      // 일반 모드일 때는 5분 단위로 반올림
      return (Math.floor(minutes / 5) * 5).toString().padStart(2, "0");
    };

    const mm = (currentDate.getMonth() + 1).toString().padStart(2, "0");
    const dd = currentDate.getDate().toString().padStart(2, "0");

    return (
      <div className="flex w-full h-10 bg-white border border-gray-200 rounded-md px-2 shadow-sm">
        {/* 날짜 */}
        <div className="flex flex-1 items-center justify-center border-r min-w-[90px] px-2">
          {!isNowMode && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => changeDate(-1)}
              className="text-gray-500 h-8 w-8 p-0 flex-shrink-0"
            >
              &#60;
            </Button>
          )}
          <span
            className={`font-semibold text-sm flex-1 text-center ${
              isNowMode ? "mx-0" : "mx-2"
            }`}
          >
            {isToday ? "Today" : `${mm}.${dd}`}
          </span>
          {!isNowMode && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => changeDate(1)}
              className="text-gray-500 h-8 w-8 p-0 flex-shrink-0"
            >
              &#62;
            </Button>
          )}
        </div>
        {/* 시 */}
        <div className="flex flex-1 items-center justify-center border-r min-w-[70px] px-2">
          {!isNowMode && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => changeHour(-1)}
              className="text-gray-500 h-8 w-8 p-0 flex-shrink-0"
            >
              &#60;
            </Button>
          )}
          <span
            className={`font-semibold text-sm flex-1 text-center ${
              isNowMode ? "mx-0" : "mx-2"
            }`}
          >
            {formatHour(currentDate)}
          </span>
          {!isNowMode && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => changeHour(1)}
              className="text-gray-500 h-8 w-8 p-0 flex-shrink-0"
            >
              &#62;
            </Button>
          )}
        </div>
        {/* 분 */}
        <div className="flex flex-1 items-center justify-center min-w-[70px] px-2">
          {!isNowMode && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => changeMinute(-5)}
              className="text-gray-500 h-8 w-8 p-0 flex-shrink-0"
            >
              &#60;
            </Button>
          )}
          <span
            className={`font-semibold text-sm flex-1 text-center ${
              isNowMode ? "mx-0" : "mx-2"
            }`}
          >
            {formatMinute(currentDate)}
          </span>
          {!isNowMode && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => changeMinute(5)}
              className="text-gray-500 h-8 w-8 p-0 flex-shrink-0"
            >
              &#62;
            </Button>
          )}
        </div>
      </div>
    );
  }
);

DateTimePicker.displayName = "DateTimePicker";
