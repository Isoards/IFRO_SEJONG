import React, { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { Button } from "./Button";
import { cn } from "../../lib/utils";

// Dialog components integrated into CalendarModal
const Dialog = DialogPrimitive.Root;

const DialogPortal = (props: DialogPrimitive.DialogPortalProps) => (
  <DialogPrimitive.Portal {...props} />
);

const DialogOverlay = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Overlay
    ref={ref}
    className={cn("fixed inset-0 z-50 bg-black/50 backdrop-blur-sm", className)}
    {...props}
  />
));

const DialogContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ className, ...props }, ref) => (
  <DialogPortal>
    <DialogOverlay />
    <DialogPrimitive.Content
      ref={ref}
      className={cn(
        "fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 sm:rounded-lg",
        className
      )}
      {...props}
    />
  </DialogPortal>
));

interface CalendarModalProps {
  isOpen?: boolean;
  onClose?: () => void;
  onDateRangeSelect?: (startDate: Date, endDate: Date) => void;
}

const CalendarModal: React.FC<CalendarModalProps> = ({
  isOpen = true,
  onClose,
  onDateRangeSelect,
}) => {
  const [currentDate, setCurrentDate] = useState(new Date(2023, 0, 1)); // January 2023
  const [startDate, setStartDate] = useState<Date | null>(
    new Date(2023, 0, 10)
  );
  const [endDate, setEndDate] = useState<Date | null>(new Date(2023, 0, 28));
  const [isSelectingEnd, setIsSelectingEnd] = useState(false);

  const monthNames = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];

  const getDaysInMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };

  const navigateMonth = (direction: "prev" | "next") => {
    setCurrentDate((prev) => {
      const newDate = new Date(prev);
      if (direction === "prev") {
        newDate.setMonth(prev.getMonth() - 1);
      } else {
        newDate.setMonth(prev.getMonth() + 1);
      }
      return newDate;
    });
  };

  const handleDateClick = (day: number) => {
    const clickedDate = new Date(
      currentDate.getFullYear(),
      currentDate.getMonth(),
      day
    );

    if (!startDate || (startDate && endDate && !isSelectingEnd)) {
      // 새로운 선택 시작
      setStartDate(clickedDate);
      setEndDate(null);
      setIsSelectingEnd(true);
    } else if (isSelectingEnd) {
      // 끝 날짜 선택
      if (clickedDate < startDate) {
        // 시작날짜보다 이전이면 순서 바꿈
        setEndDate(startDate);
        setStartDate(clickedDate);
      } else {
        setEndDate(clickedDate);
      }
      setIsSelectingEnd(false);

      // 콜백 호출
      if (onDateRangeSelect) {
        const finalStart = clickedDate < startDate ? clickedDate : startDate;
        const finalEnd = clickedDate < startDate ? startDate : clickedDate;
        onDateRangeSelect(finalStart, finalEnd);
      }
    }
  };

  const isDateInRange = (day: number) => {
    if (!startDate || !endDate) return false;
    const currentDateObj = new Date(
      currentDate.getFullYear(),
      currentDate.getMonth(),
      day
    );
    return currentDateObj >= startDate && currentDateObj <= endDate;
  };

  const isDateRangeEnd = (day: number) => {
    if (!startDate) return false;
    const currentDateObj = new Date(
      currentDate.getFullYear(),
      currentDate.getMonth(),
      day
    );

    const isStart =
      startDate &&
      currentDateObj.getFullYear() === startDate.getFullYear() &&
      currentDateObj.getMonth() === startDate.getMonth() &&
      currentDateObj.getDate() === startDate.getDate();

    const isEnd =
      endDate &&
      currentDateObj.getFullYear() === endDate.getFullYear() &&
      currentDateObj.getMonth() === endDate.getMonth() &&
      currentDateObj.getDate() === endDate.getDate();

    return isStart || isEnd;
  };

  const handleQuickSelect = (type: string) => {
    const today = new Date();
    const currentYear = today.getFullYear();
    const currentMonth = today.getMonth();
    const currentDay = today.getDate();

    let startDateObj: Date, endDateObj: Date;

    switch (type) {
      case "today":
        startDateObj = endDateObj = new Date(
          currentYear,
          currentMonth,
          currentDay
        );
        setCurrentDate(new Date(currentYear, currentMonth, 1));
        break;
      case "yesterday":
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        startDateObj = endDateObj = yesterday;
        setCurrentDate(
          new Date(yesterday.getFullYear(), yesterday.getMonth(), 1)
        );
        break;
      case "lastWeek":
        const weekStart = new Date(today);
        weekStart.setDate(today.getDate() - 7);
        const weekEnd = new Date(today);
        weekEnd.setDate(today.getDate() - 1);
        startDateObj = weekStart;
        endDateObj = weekEnd;
        setCurrentDate(
          new Date(weekStart.getFullYear(), weekStart.getMonth(), 1)
        );
        break;
      case "lastMonth":
        const lastMonthStart = new Date(currentYear, currentMonth - 1, 1);
        const lastMonthEnd = new Date(currentYear, currentMonth, 0);
        startDateObj = lastMonthStart;
        endDateObj = lastMonthEnd;
        setCurrentDate(
          new Date(lastMonthStart.getFullYear(), lastMonthStart.getMonth(), 1)
        );
        break;
      case "lastQuarter":
        const quarterStart = new Date(currentYear, currentMonth - 3, 1);
        const quarterEnd = new Date(currentYear, currentMonth, 0);
        startDateObj = quarterStart;
        endDateObj = quarterEnd;
        setCurrentDate(
          new Date(quarterStart.getFullYear(), quarterStart.getMonth(), 1)
        );
        break;
      default:
        return;
    }

    setStartDate(startDateObj);
    setEndDate(endDateObj);
    setIsSelectingEnd(false);

    // 콜백 호출
    if (onDateRangeSelect) {
      onDateRangeSelect(startDateObj, endDateObj);
    }
  };

  const handleReset = () => {
    setStartDate(null);
    setEndDate(null);
    setIsSelectingEnd(false);
    setCurrentDate(new Date());
  };

  const renderCalendarDays = () => {
    const daysInMonth = getDaysInMonth(currentDate);
    const firstDay = getFirstDayOfMonth(currentDate);
    const days = [];

    // Previous month's trailing days
    const prevMonth = new Date(
      currentDate.getFullYear(),
      currentDate.getMonth() - 1,
      0
    );
    const prevMonthDays = prevMonth.getDate();

    for (let i = firstDay - 1; i >= 0; i--) {
      days.push(
        <Button
          key={`prev-${prevMonthDays - i}`}
          variant="ghost"
          className="w-8 h-8 text-gray-400 text-sm"
          onClick={() => {
            /* 이전 달 날짜 클릭 처리 가능 */
          }}
        >
          {prevMonthDays - i}
        </Button>
      );
    }

    // Current month days
    for (let day = 1; day <= daysInMonth; day++) {
      let buttonClass = "w-8 h-8 rounded text-sm transition-colors ";

      if (isDateRangeEnd(day)) {
        buttonClass += "bg-blue-500 text-white hover:bg-blue-600 ";
      } else if (isDateInRange(day)) {
        buttonClass += "bg-blue-100 text-blue-700 hover:bg-blue-200 ";
      } else {
        buttonClass += "text-gray-700 hover:bg-gray-100 ";
      }

      days.push(
        <Button
          key={day}
          variant="ghost"
          className={buttonClass}
          onClick={() => handleDateClick(day)}
        >
          {day}
        </Button>
      );
    }

    // Next month's leading days
    const totalCells = Math.ceil((firstDay + daysInMonth) / 7) * 7;
    const remainingCells = totalCells - (firstDay + daysInMonth);

    for (let day = 1; day <= remainingCells; day++) {
      days.push(
        <Button
          key={`next-${day}`}
          variant="ghost"
          className="w-8 h-8 text-gray-400 text-sm"
          onClick={() => {
            /* 다음 달 날짜 클릭 처리 가능 */
          }}
        >
          {day}
        </Button>
      );
    }

    return days;
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md p-0 flex relative max-h-[90vh] overflow-auto fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white/95 shadow-2xl border border-gray-200 rounded-xl z-[9999]">
        {/* Left Sidebar */}
        <div className="w-32 bg-gray-50 p-4 rounded-l-lg border-r">
          <div className="space-y-2">
            <Button
              variant="ghost"
              className="block w-full text-left text-sm text-gray-700 hover:text-gray-900 py-1"
              onClick={() => handleQuickSelect("today")}
            >
              Today
            </Button>
            <Button
              variant="ghost"
              className="block w-full text-left text-sm text-gray-700 hover:text-gray-900 py-1"
              onClick={() => handleQuickSelect("yesterday")}
            >
              Yesterday
            </Button>
            <Button
              variant="ghost"
              className="block w-full text-left text-sm text-gray-700 hover:text-gray-900 py-1"
              onClick={() => handleQuickSelect("lastWeek")}
            >
              Last week
            </Button>
            <Button
              variant="ghost"
              className="block w-full text-left text-sm text-gray-700 hover:text-gray-900 py-1"
              onClick={() => handleQuickSelect("lastMonth")}
            >
              Last month
            </Button>
            <Button
              variant="ghost"
              className="block w-full text-left text-sm text-gray-700 hover:text-gray-900 py-1"
              onClick={() => handleQuickSelect("lastQuarter")}
            >
              Last quarter
            </Button>
          </div>

          <div className="mt-16">
            <Button
              variant="link"
              className="text-blue-500 text-sm font-medium hover:text-blue-600"
              onClick={handleReset}
            >
              Reset
            </Button>
          </div>
        </div>

        {/* Right Calendar */}
        <div className="flex-1 p-4">
          {/* Calendar Header */}
          <div className="flex items-center justify-between mb-4 pr-10">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigateMonth("prev")}
              className="p-1"
            >
              <ChevronLeft className="w-4 h-4 text-gray-600" />
            </Button>
            <h2 className="text-lg font-medium text-gray-900">
              {monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}
            </h2>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigateMonth("next")}
              className="p-1"
            >
              <ChevronRight className="w-4 h-4 text-gray-600" />
            </Button>
          </div>

          {/* Calendar Grid */}
          <div className="mb-4">
            {/* Day headers */}
            <div className="grid grid-cols-7 gap-1 mb-2">
              {["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"].map((day) => (
                <div
                  key={day}
                  className="text-center text-xs text-gray-500 font-medium py-1"
                >
                  {day}
                </div>
              ))}
            </div>

            {/* Calendar days */}
            <div className="grid grid-cols-7 gap-1">{renderCalendarDays()}</div>
          </div>
        </div>

        {/* Close button */}
        {onClose && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="absolute top-2 right-4 text-gray-400 hover:text-gray-600 text-xl font-bold"
            aria-label="Close"
          >
            ×
          </Button>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default CalendarModal;
