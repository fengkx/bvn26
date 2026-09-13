# Duration mismatch in first catalog capture

The first original catalog capture uses the shared dynamic probe built for 360 fight ticks, while its generated `move_cases` fixture defaulted to 300 ticks. The source input windows and setup were correct and unchanged; only the end-of-case observation tail differed. The retained initial comparison shows 722 source rows versus 602 port rows and zero differing states among those observed.

`duration-normalized-comparison.json` uses a derived port fixture with `frames: 360`, adding 60 observation ticks with no scheduled inputs. This matches the original source run duration without truncating source or changing input timing. The unmodified generated 300-tick fixture remains in the catalog fixture directory; the capture case and build metadata remain retained as captured.
