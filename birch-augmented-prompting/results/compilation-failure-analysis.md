# Compilation Failure Analysis

#### 1. Hallucinated APIs
**Example - Bug Chart-18**:

Buggy Code:
```
public void removeColumn(Comparable columnKey) {
<START_BUG>
        Iterator iterator = this.rows.iterator();
        while (iterator.hasNext()) {
            DefaultKeyedValues rowData = (DefaultKeyedValues) iterator.next();
                rowData.removeValue(columnKey);
<END_BUG>
        }
        this.columnKeys.remove(columnKey);
    }
```

Generated Code:
```
public void removeColumn(Comparable columnKey) {
    Iterator iterator = this.rows.iterator();
    while (iterator.hasNext()) {
        DefaultKeyedValues rowData = (DefaultKeyedValues) iterator.next();
        if (rowData.containsKey(columnKey)) {
            rowData.removeValue(columnKey);
        }
    }
    this.columnKeys.remove(columnKey);
}
```

Error Message:
```
    [javac] Compiling 577 source files to /Users/danielding/Desktop/test-region/birch1/birch/~/Desktop/Chart_18/build
    [javac] /Users/danielding/Desktop/test-region/birch1/birch/~/Desktop/Chart_18/source/org/jfree/data/DefaultKeyedValues2D.java:458: error: cannot find symbol
    [javac]         if (rowData.containsKey(columnKey)) {
    [javac]                    ^
    [javac]   symbol:   method containsKey(Comparable)
    [javac]   location: variable rowData of type DefaultKeyedValues
    [javac] 1 error
    [javac] 100 warnings
```

There is no method called containsKey in class DefaultedKeyedValues

#### 2. Java Version Mismatch
**Example - Cli 33**

Buggy code:
```
public void printWrapped(PrintWriter pw, int width, int nextLineTabStop, String text)
    {
        StringBuffer sb = new StringBuffer(text.length());

<START_BUG>
        renderWrappedText(sb, width, nextLineTabStop, text);
<END_BUG>
        pw.println(sb.toString());
    }
```

Generated Code:
```
public void printWrapped(PrintWriter pw, int width, int nextLineTabStop, String text)
{
    StringBuffer sb = new StringBuffer(text.length());
    String[] lines = text.split("\n");
    for (String line : lines) {
        if (line.startsWith(" ")) {
            sb.append(line);
        } else {
            renderWrappedText(sb, width, nextLineTabStop, line);
        }
        sb.append("\n");
    }
    pw.println(sb.toString().trim());
}
```

Error Message:
```
    [javac] Compiling 22 source files to /private/tmp/work_dir/Cli_33/target/classes
    [javac] /private/tmp/work_dir/Cli_33/src/main/java/org/apache/commons/cli/HelpFormatter.java:730: error: for-each loops are not supported in -source 1.4
    [javac]     for (String line : lines) {
    [javac]                      ^
    [javac]   (use -source 5 or higher to enable for-each loops)
    [javac] 1 error
    [javac] 1 warning
```

#### 3. <START_BUG> and <END_BUG> markers being present in the generated code.
**Example - Time 10**
Buggy Code:
```
protected static int between(ReadablePartial start, ReadablePartial end, ReadablePeriod zeroInstance) {
        if (start == null || end == null) {
            throw new IllegalArgumentException("ReadablePartial objects must not be null");
        }
        if (start.size() != end.size()) {
            throw new IllegalArgumentException("ReadablePartial objects must have the same set of fields");
        }
        for (int i = 0, isize = start.size(); i < isize; i++) {
            if (start.getFieldType(i) != end.getFieldType(i)) {
                throw new IllegalArgumentException("ReadablePartial objects must have the same set of fields");
            }
        }
        if (DateTimeUtils.isContiguous(start) == false) {
            throw new IllegalArgumentException("ReadablePartial objects must be contiguous");
        }
        Chronology chrono = DateTimeUtils.getChronology(start.getChronology()).withUTC();
<START_BUG>
        int[] values = chrono.get(zeroInstance, chrono.set(start, 0L), chrono.set(end, 0L));
<END_BUG>
        return values[0];
    }
```
Generated Code:
```
protected static int between(ReadablePartial start, ReadablePartial end, ReadablePeriod zeroInstance) {
    if (start == null || end == null) {
        throw new IllegalArgumentException("ReadablePartial objects must not be null");
    }
    if (start.size() != end.size()) {
        throw new IllegalArgumentException("ReadablePartial objects must have the same set of fields");
    }
    for (int i = 0, isize = start.size(); i < isize; i++) {
        if (start.getFieldType(i) != end.getFieldType(i)) {
            throw new IllegalArgumentException("ReadablePartial objects must have the same set of fields");
        }
    }
    if (DateTimeUtils.isContiguous(start) == false) {
        throw new IllegalArgumentException("ReadablePartial objects must be contiguous");
    }
    Chronology chrono = DateTimeUtils.getChronology(start.getChronology()).withUTC();
    <START_BUG>
    LocalDate startDate = new LocalDate(start.getChronology().era().get(start), start.getChronology().year().get(start), 1);
    LocalDate endDate = new LocalDate(end.getChronology().era().get(end), end.getChronology().year().get(end), 1);
    for (int i = 0, isize = start.size(); i < isize; i++) {
        if (start.getFieldType(i).equals(DateTimeFieldType.monthOfYear())) {
            startDate = startDate.withMonthOfYear(start.getField(i).getValue());
        } else if (start.getFieldType(i).equals(DateTimeFieldType.dayOfMonth())) {
            if (start.getField(i).getValue() > 28) {
                startDate = startDate.withDayOfMonth(28);
            } else {
                startDate = startDate.withDayOfMonth(start.getField(i).getValue());
            }
            if (end.getField(i).getValue() > 28) {
                endDate = endDate.withDayOfMonth(28);
            } else {
                endDate = endDate.withDayOfMonth(end.getField(i).getValue());
            }
        }
    }
    int[] values = chrono.get(zeroInstance, chrono.set(startDate, 0L), chrono.set(endDate, 0L));
    <END_BUG>
    return values[0];
}
```
Error Message:
```
    [javac] Compiling 157 source files to /private/tmp/work_dir/Time_10/target/classes
    [javac] Picked up JAVA_TOOL_OPTIONS: -Duser.language=en -Duser.country=US
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:52: error: illegal start of type
    [javac] if (start instanceof MonthDay && end instanceof MonthDay) {
    [javac] ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:52: error: <identifier> expected
    [javac] if (start instanceof MonthDay && end instanceof MonthDay) {
    [javac]          ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:52: error: ';' expected
    [javac] if (start instanceof MonthDay && end instanceof MonthDay) {
    [javac]                     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:52: error: illegal start of type
    [javac] if (start instanceof MonthDay && end instanceof MonthDay) {
    [javac]                               ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:52: error: ';' expected
    [javac] if (start instanceof MonthDay && end instanceof MonthDay) {
    [javac]                                     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:52: error: <identifier> expected
    [javac] if (start instanceof MonthDay && end instanceof MonthDay) {
    [javac]                                                         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:66: error: illegal start of type
    [javac] } else {
    [javac]   ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:66: error: ';' expected
    [javac] } else {
    [javac]       ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:67: error: illegal start of type
    [javac]     return super.between(start, end);
    [javac]     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:67: error: <identifier> expected
    [javac]     return super.between(start, end);
    [javac]           ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:67: error: ';' expected
    [javac]     return super.between(start, end);
    [javac]                 ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:67: error: invalid method declaration; return type required
    [javac]     return super.between(start, end);
    [javac]                  ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:67: error: <identifier> expected
    [javac]     return super.between(start, end);
    [javac]                               ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:67: error: <identifier> expected
    [javac]     return super.between(start, end);
    [javac]                                    ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:70: error: class, interface, or enum expected
    [javac]     private volatile int iPeriod;
    [javac]                      ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:82: error: class, interface, or enum expected
    [javac]     protected static int between(ReadableInstant start, ReadableInstant end, DurationFieldType field) {
    [javac]                      ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:85: error: class, interface, or enum expected
    [javac]         }
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:87: error: class, interface, or enum expected
    [javac]         int amount = field.getField(chrono).getDifference(end.getMillis(), start.getMillis());
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:88: error: class, interface, or enum expected
    [javac]         return amount;
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:89: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:107: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:110: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:111: error: class, interface, or enum expected
    [javac]     for (int i = 0, isize = start.size(); i < isize; i++) {
    [javac]                                           ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:111: error: class, interface, or enum expected
    [javac]     for (int i = 0, isize = start.size(); i < isize; i++) {
    [javac]                                                      ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:114: error: class, interface, or enum expected
    [javac]         }
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:118: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:120: error: class, interface, or enum expected
    [javac]     <START_BUG>
    [javac]     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:122: error: class, interface, or enum expected
    [javac]     LocalDate endDate = new LocalDate(end.getChronology().era().get(end), end.getChronology().year().get(end), 1);
    [javac]     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:123: error: class, interface, or enum expected
    [javac]     for (int i = 0, isize = start.size(); i < isize; i++) {
    [javac]     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:123: error: class, interface, or enum expected
    [javac]     for (int i = 0, isize = start.size(); i < isize; i++) {
    [javac]                                           ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:123: error: class, interface, or enum expected
    [javac]     for (int i = 0, isize = start.size(); i < isize; i++) {
    [javac]                                                      ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:126: error: class, interface, or enum expected
    [javac]         } else if (start.getFieldType(i).equals(DateTimeFieldType.dayOfMonth())) {
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:129: error: class, interface, or enum expected
    [javac]             } else {
    [javac]             ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:131: error: class, interface, or enum expected
    [javac]             }
    [javac]             ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:134: error: class, interface, or enum expected
    [javac]             } else {
    [javac]             ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:136: error: class, interface, or enum expected
    [javac]             }
    [javac]             ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:140: error: class, interface, or enum expected
    [javac]     <END_BUG>
    [javac]     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:142: error: class, interface, or enum expected
    [javac] }
    [javac] ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:167: error: class, interface, or enum expected
    [javac]         }
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:169: error: class, interface, or enum expected
    [javac]         long duration = 0L;
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:170: error: class, interface, or enum expected
    [javac]         for (int i = 0; i < period.size(); i++) {
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:170: error: class, interface, or enum expected
    [javac]         for (int i = 0; i < period.size(); i++) {
    [javac]                         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:170: error: class, interface, or enum expected
    [javac]         for (int i = 0; i < period.size(); i++) {
    [javac]                                            ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:172: error: class, interface, or enum expected
    [javac]             if (value != 0) {
    [javac]             ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:174: error: class, interface, or enum expected
    [javac]                 if (field.isPrecise() == false) {
    [javac]                 ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:178: error: class, interface, or enum expected
    [javac]                 }
    [javac]                 ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:180: error: class, interface, or enum expected
    [javac]             }
    [javac]             ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:183: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:193: error: class, interface, or enum expected
    [javac]         iPeriod = period;
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:194: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:204: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:214: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:222: error: class, interface, or enum expected
    [javac]     public abstract DurationFieldType getFieldType();
    [javac]                     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:229: error: class, interface, or enum expected
    [javac]     public abstract PeriodType getPeriodType();
    [javac]                     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:237: error: class, interface, or enum expected
    [javac]     public int size() {
    [javac]            ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:239: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:251: error: class, interface, or enum expected
    [javac]     public DurationFieldType getFieldType(int index) {
    [javac]            ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:254: error: class, interface, or enum expected
    [javac]         }
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:256: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:267: error: class, interface, or enum expected
    [javac]     public int getValue(int index) {
    [javac]            ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:270: error: class, interface, or enum expected
    [javac]         }
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:272: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:283: error: class, interface, or enum expected
    [javac]     public int get(DurationFieldType type) {
    [javac]            ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:286: error: class, interface, or enum expected
    [javac]         }
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:288: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:296: error: class, interface, or enum expected
    [javac]     public boolean isSupported(DurationFieldType type) {
    [javac]            ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:298: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:307: error: class, interface, or enum expected
    [javac]     public Period toPeriod() {
    [javac]            ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:309: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:319: error: class, interface, or enum expected
    [javac]     public MutablePeriod toMutablePeriod() {
    [javac]            ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:321: error: class, interface, or enum expected
    [javac]         period.add(this);
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:322: error: class, interface, or enum expected
    [javac]         return period;
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:323: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:335: error: class, interface, or enum expected
    [javac]     public boolean equals(Object period) {
    [javac]            ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:338: error: class, interface, or enum expected
    [javac]         }
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:341: error: class, interface, or enum expected
    [javac]         }
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:343: error: class, interface, or enum expected
    [javac]         return (other.getPeriodType() == getPeriodType() && other.getValue(0) == getValue());
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:344: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:351: error: class, interface, or enum expected
    [javac]     public int hashCode() {
    [javac]            ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:353: error: class, interface, or enum expected
    [javac]         total = 27 * total + getValue();
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:354: error: class, interface, or enum expected
    [javac]         total = 27 * total + getFieldType().hashCode();
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:355: error: class, interface, or enum expected
    [javac]         return total;
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:356: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:366: error: class, interface, or enum expected
    [javac]     public int compareTo(BaseSingleFieldPeriod other) {
    [javac]            ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:369: error: class, interface, or enum expected
    [javac]         }
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:371: error: class, interface, or enum expected
    [javac]         int thisValue = getValue();
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:372: error: class, interface, or enum expected
    [javac]         if (thisValue > otherValue) {
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:374: error: class, interface, or enum expected
    [javac]         }
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:377: error: class, interface, or enum expected
    [javac]         }
    [javac]         ^
    [javac] /private/tmp/work_dir/Time_10/src/main/java/org/joda/time/base/BaseSingleFieldPeriod.java:379: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] 90 errors
    [javac] 4 warnings
```
#### 4. Incomplete Scope Gathering
**Example - Mockito 16**

Buggy Code:
```
<START_BUG>
public <T> T mock(Class<T> classToMock, MockSettings mockSettings, boolean shouldResetOngoingStubbing) { return mock(classToMock, mockSettings); }
    public <T> T mock(Class<T> classToMock, MockSettings mockSettings) {
        mockingProgress.validateState();
            mockingProgress.resetOngoingStubbing();
<END_BUG>
```

Generated Code:
```
public <T> T mock(Class<T> classToMock, MockSettings mockSettings, boolean shouldResetOngoingStubbing) { 
    T mock = mock(classToMock, mockSettings); 
    if (shouldResetOngoingStubbing) {
        mockingProgress.resetOngoingStubbing();
    }
    return mock;
}
public <T> T mock(Class<T> classToMock, MockSettings mockSettings) {
    mockingProgress.validateState();
    T mock = createMock(classToMock, mockSettings);
    mockingProgress.resetOngoingStubbing();
    return mock;
}
```

Error Message:
```
    [javac] Compiling 199 source files to /private/tmp/work_dir/Mockito_16/target/classes
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:45: error: illegal start of type
    [javac]         return mockUtil.createMock(classToMock, (MockSettingsImpl) mockSettings);
    [javac]         ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:45: error: ';' expected
    [javac]         return mockUtil.createMock(classToMock, (MockSettingsImpl) mockSettings);
    [javac]               ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:45: error: illegal start of type
    [javac]         return mockUtil.createMock(classToMock, (MockSettingsImpl) mockSettings);
    [javac]                        ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:45: error: <identifier> expected
    [javac]         return mockUtil.createMock(classToMock, (MockSettingsImpl) mockSettings);
    [javac]                                               ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:45: error: illegal start of type
    [javac]         return mockUtil.createMock(classToMock, (MockSettingsImpl) mockSettings);
    [javac]                                                 ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:45: error: ')' expected
    [javac]         return mockUtil.createMock(classToMock, (MockSettingsImpl) mockSettings);
    [javac]                                                  ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:45: error: ';' expected
    [javac]         return mockUtil.createMock(classToMock, (MockSettingsImpl) mockSettings);
    [javac]                                                                  ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:45: error: <identifier> expected
    [javac]         return mockUtil.createMock(classToMock, (MockSettingsImpl) mockSettings);
    [javac]                                                                                ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:48: error: class, interface, or enum expected
    [javac]     public IOngoingStubbing stub() {
    [javac]            ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:50: error: class, interface, or enum expected
    [javac]         if (stubbing == null) {
    [javac]         ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:52: error: class, interface, or enum expected
    [javac]             reporter.missingMethodInvocation();
    [javac]             ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:53: error: class, interface, or enum expected
    [javac]         }
    [javac]         ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:55: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:58: error: class, interface, or enum expected
    [javac]     public <T> DeprecatedOngoingStubbing<T> stub(T methodCall) {
    [javac]            ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:60: error: class, interface, or enum expected
    [javac]         return (DeprecatedOngoingStubbing) stub();
    [javac]         ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:61: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:63: error: class, interface, or enum expected
    [javac]     public <T> OngoingStubbing<T> when(T methodCall) {
    [javac]            ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:65: error: class, interface, or enum expected
    [javac]         return (OngoingStubbing) stub();
    [javac]         ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:66: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:69: error: class, interface, or enum expected
    [javac]     public <T> T verify(T mock, VerificationMode mode) {
    [javac]            ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:72: error: class, interface, or enum expected
    [javac]         } else if (!mockUtil.isMock(mock)) {
    [javac]         ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:74: error: class, interface, or enum expected
    [javac]         }
    [javac]         ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:76: error: class, interface, or enum expected
    [javac]         return mock;
    [javac]         ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:77: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:79: error: class, interface, or enum expected
    [javac]     public <T> void reset(T ... mocks) {
    [javac]            ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:81: error: class, interface, or enum expected
    [javac]         mockingProgress.reset();
    [javac]         ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:82: error: class, interface, or enum expected
    [javac]         mockingProgress.resetOngoingStubbing();
    [javac]         ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:84: error: class, interface, or enum expected
    [javac]         for (T m : mocks) {
    [javac]         ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:86: error: class, interface, or enum expected
    [javac]         }
    [javac]         ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:89: error: class, interface, or enum expected
    [javac]     public void verifyNoMoreInteractions(Object... mocks) {
    [javac]            ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:91: error: class, interface, or enum expected
    [javac]         mockingProgress.validateState();
    [javac]         ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:92: error: class, interface, or enum expected
    [javac]         for (Object mock : mocks) {
    [javac]         ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:96: error: class, interface, or enum expected
    [javac]                 }
    [javac]                 ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:98: error: class, interface, or enum expected
    [javac]             } catch (NotAMockException e) {
    [javac]             ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:100: error: class, interface, or enum expected
    [javac]             }
    [javac]             ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:107: error: class, interface, or enum expected
    [javac]         }
    [javac]         ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:110: error: class, interface, or enum expected
    [javac]     public InOrder inOrder(Object... mocks) {
    [javac]            ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:113: error: class, interface, or enum expected
    [javac]         }
    [javac]         ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:117: error: class, interface, or enum expected
    [javac]             } else if (!mockUtil.isMock(mock)) {
    [javac]             ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:119: error: class, interface, or enum expected
    [javac]             }
    [javac]             ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:122: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:124: error: class, interface, or enum expected
    [javac]     public Stubber doAnswer(Answer answer) {
    [javac]            ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:126: error: class, interface, or enum expected
    [javac]         mockingProgress.resetOngoingStubbing();
    [javac]         ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:127: error: class, interface, or enum expected
    [javac]         return new StubberImpl().doAnswer(answer);
    [javac]         ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:128: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:130: error: class, interface, or enum expected
    [javac]     public <T> VoidMethodStubbable<T> stubVoid(T mock) {
    [javac]            ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:132: error: class, interface, or enum expected
    [javac]         mockingProgress.stubbingStarted();
    [javac]         ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:133: error: class, interface, or enum expected
    [javac]         return handler.voidMethodStubbable(mock);
    [javac]         ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:134: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:136: error: class, interface, or enum expected
    [javac]     public void validateMockitoUsage() {
    [javac]            ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:138: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:144: error: class, interface, or enum expected
    [javac]     public Invocation getLastInvocation() {
    [javac]            ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:146: error: class, interface, or enum expected
    [javac]         List<Invocation> allInvocations = ongoingStubbing.getRegisteredInvocations();
    [javac]         ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:147: error: class, interface, or enum expected
    [javac]         return allInvocations.get(allInvocations.size()-1);
    [javac]         ^
    [javac] /private/tmp/work_dir/Mockito_16/src/org/mockito/internal/MockitoCore.java:148: error: class, interface, or enum expected
    [javac]     }
    [javac]     ^
    [javac] 55 errors
    [javac] 1 warning
```