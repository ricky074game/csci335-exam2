# 00 - Exam 2 cheat sheet (read the morning of Nov 19)

> Exam 2: Thu Nov 19, seated by 2:30 PM, 70 min, closed book, ~100 pts. About **half the points = complexity analysis
> (incl. design) + coding** (cumulative); the rest = hashing / heaps / sorting traces and properties.
> **Use the textbook algorithms only**: other "valid" variants are graded wrong.

## 1. Master complexity table

| Structure / algorithm | Operation | Cost | One-line reason |
|---|---|---|---|
| vector | `v[k]`, `push_back` | O(1), amortized O(1) | address arithmetic; doubling copies average out |
| vector | insert/erase in middle, `find` | O(n) | shift / walk |
| list | insert/erase at an iterator | O(1) | relink two neighbours |
| list | reach k-th, `find` | O(n) | follow pointers |
| set / map (balanced BST) | insert, erase, find, `lower_bound`, `[]` | O(log n) | tree height is log n |
| unordered_set / unordered_map | insert, erase, find, count, `[]` | **avg O(1), worst O(n)** | hash to a bucket; all keys colliding = n |
| unordered_* | rehash (one insert) | O(n) once, amortized O(1) | re-insert every element into nextPrime(2N) |
| unordered_* | min / max / range / in-order | O(n) | hashes are unordered |
| priority_queue (binary heap) | push | O(log n) worst, O(1) avg | percolate up, on average ~1.6 levels |
| priority_queue | pop (deleteMin/Max) | O(log n) worst **and** avg | the moved last element sinks almost to the bottom |
| priority_queue | top | O(1) | root |
| binary heap | buildHeap / `make_heap` | **O(n)** | sum of node heights < n |
| binary heap | find / remove arbitrary value | O(n) find (remove(p) O(log n) if you know p) | heap order says nothing about siblings |
| AVL | insert / find / remove | O(log n) worst | height ≤ 1.44 log n |
| splay | any op | O(log n) **amortized**, O(n) single op | M ops cost O(M log n) total |
| insertion sort | | O(n²) worst/avg, O(n) sorted | one shift per inversion; avg inversions n(n−1)/4 |
| mergesort | | O(n log n) always, O(n) extra, stable | log n levels × O(n) merge |
| heapsort | | O(n log n) always, O(1) extra, not stable | buildHeap O(n) + n deleteMax × O(log n) |
| quicksort | | O(n log n) avg, **O(n²) worst**, in place, not stable | worst = pivot always min/max |
| introsort (`std::sort`) | | O(n log n) worst | quicksort → heapsort past ~2 log n depth; insertion sort under ~16 |
| quickselect | k-th smallest | **O(n) avg**, O(n²) worst | recurse into ONE side |
| heap selection | buildHeap + k deleteMin | O(n + k log n) | median: O(n log n) |
| heap selection (size-k heap) | k-th largest | O(n log k) | keep k best; compare with the root |
| counting sort (light) | | O(n + k) | k = range of keys |
| any comparison sort | lower bound | **Ω(n log n)** | decision tree has n! leaves, depth ≥ ⌈log n!⌉ |

Fundamental operations: merge O(n) · partition O(n) · percolateUp/Down O(log n) · buildHeap O(n) ·
deleteMax O(log n) · insertion-sort pass p O(p).

## 2. Hashing (Ch 5.1-5.6)

- hash(x) = x mod TableSize. Probe i: h_i(x) = (hash(x) + f(i)) mod TableSize.
  **linear** f(i)=i · **quadratic** f(i)=i² · **double** f(i)=i·hash2(x), **hash2(x) = R − (x mod R)**, R prime < TableSize (HW: 7).
- Separate chaining: new keys **appended at the end** of the list. λ ≈ 1 is fine (rehash when λ > 1).
- Probing: keep **λ ≤ 0.5** (rehash when currentSize > TableSize/2). New size = **nextPrime(2·old)**; re-insert old
  items in old-index order with the new mod. Gives up after TableSize probes: **"cannot place"** (HW5 5.1d: 1989).
- Quadratic probing: prime size + λ ≤ 0.5 ⇒ an insert always succeeds (Theorem 5.1). Non-prime size can fail early.
- **Primary clustering** = linear (blocks of occupied cells grow). **Secondary clustering** = quadratic (same home ⇒
  same probe sequence). Double hashing avoids both (step depends on the key).
- Lazy deletion: mark DELETED; searches walk past it; the textbook insert goes to the first EMPTY cell and
  `++currentSize` on every insert (remove never decrements). Exercise 5.7 variant reuses DELETED cells.
- Hashes are not ordered: no min/max, no range search, no sorted iteration.
- HW5 5.1 (sizes 10, keys 4371,1323,6173,4199,4344,9679,1989):
  chain `1:[4371] 3:[1323,6173] 4:[4344] 9:[4199,9679,1989]` · linear `0:9679 1:4371 2:1989 3:1323 4:6173 5:4344 9:4199` ·
  quadratic `0:9679 1:4371 3:1323 4:6173 5:4344 8:1989 9:4199` · double `... 5:9679 7:4344`, 1989 cannot be placed.

## 3. Binary heap (Ch 6.1-6.4)

- Complete tree in an array: **index 0 unused** (holds the value being moved), root 1, children **2i, 2i+1**, parent
  **i/2**, depth D at indices 2^D … 2^(D+1)−1. Height ⌊log n⌋. Leaves = indices n/2+1 … n.
- **insert**: hole at index n+1, x in [0]; while x < parent: slide parent down (strict <). Show the array after each slide.
- **deleteMin**: root out, last element into [0], hole at 1; move the **smaller child** up (ties → **left**) while it
  is < the moving value; drop the value in the hole.
<!-- HOLD hw6 -->
  HW6 Q2: `3,6,5,7,12,9,13,11,8` → `5,6,8,7,12,9,13,11`.
<!-- /HOLD -->
- **buildHeap**: percolateDown(i) for i = n/2 down to 1. O(n) because Σ heights < n
  (n/4·1 + n/8·2 + n/16·3 + … = n). 6.2b: `10,12,1,14,6,5,8,15,3,9,7,4,11,13,2` → `1,3,2,12,6,4,8,15,14,9,7,5,11,13,10`.
- decreaseKey → percolate up; increaseKey → percolate down; remove(p) = decreaseKey(p, ∞) + deleteMin.
- A max element of a min-heap is at a leaf (second half of the array). A priority queue is the ADT; a heap is one DS.

## 4. Heapsort (7.5, Fig 7.10): DIFFERENT layout

- **0-indexed MAX-heap** inside the array: leftChild(i) = **2i+1**; buildHeap for i = n/2−1 down to 0; then for
  j = n−1 down to 1: **swap(a[0], a[j]); percDown(a, 0, j)**. Sorted part grows from the right.
- `31,41,59,26,53,58,97` → after buildHeap `97,53,59,26,41,58,31` → after 1st deleteMax `59,53,58,26,41,31 | 97`.
- Analysis (professor's wording): buildHeap O(n) + n deleteMax × O(log n) = **O(n log n)**; in place; not stable.
- `std::make_heap` O(n), `pop_heap` O(log n) moves the max to the end: myHeapSort = make_heap, then pop_heap n times.

## 5. Quicksort / quickselect: Hoare partition (textbook 7.7.2, HW7, handout)

1. Pivot = median of a[left], a[center], a[right], center = (left+right)/2 (or the given position) → **swap it with
   the LAST element**.
2. i = left, j = right−1. i skips elements **< pivot**, j skips elements **> pivot**. **Both stop on equal.**
3. i < j → swap, keep going. Crossed → **swap a[i] with the pivot**. Pivot is now final; recurse on both sides.
- Cutoff (HW7 7.19): subarray size ≤ 3 → insertion sort. Textbook 7.7.2 example `8,1,4,9,6,3,5,2,7,0` →
  `2,1,4,5,0,3,6,8,7,9`. Handout: pivot "position 4" = value 9 = **index 3** (1-based position).
- Pivot choice: first element = **horrible** on sorted input (O(n²)); random = safe but costs; median-of-3 = standard.
<!-- HOLD hw7 -->
  Picking the minimum of the 3 by mistake: still correct, but worst-case O(n²) on sorted input (HW7 B).
<!-- /HOLD -->
- Equal keys: both stop ⇒ many swaps but balanced splits ⇒ O(n log n) on all-equal input; not stopping ⇒ O(n²).
- C++ code version (Fig 7.16/7.17): median3 *sorts* the three and hides the pivot at right−1; same idea.
- **Quickselect** (k 1-based): partition; **k ≤ i → left**; **k = i+1 → pivot is the answer**; else right.
  O(n) avg (T(n) = T(n/2) + n), O(n²) worst.
- Recurrences: worst T(n) = T(n−1) + cn = O(n²); best T(n) = 2T(n/2) + cn = O(n log n); average O(n log n)
  (telescoping, harmonic sum); quickselect average T(n) = T(n−1)+2c ⇒ O(n).

## 6. Other sorts and bounds

- Insertion sort: pass p puts a[p] among a[0..p]; swaps = inversions; Ω(n²) for every adjacent-swap sort.
- Mergesort: center = (left+right)/2 (left half gets the extra), merge takes the left on ties ⇒ stable;
  T(n) = 2T(n/2) + n ⇒ n log n + n.
- Stable: insertion, merge. Not stable: heapsort, quicksort. In place: insertion, heap, quick (log n stack). Not: merge.
- Lower bound: ⌈log₂(n!)⌉ comparisons in the worst case = Ω(n log n) (Lemma: depth d tree has ≤ 2^d leaves).

## 7. Design / analysis answer template (half the exam)

1. Name the operations the problem needs (lookup? order? min/max? range? k-th?).
2. Pick the structure whose operations are cheapest **and say why the others lose**.
3. Cost of every step: per-operation cost (cite it: "unordered_map find is O(1) average") × how many times.
4. Add the steps → total. **Average vs worst** for hashing. Several variables if the problem has them (O(n + k log n)).
5. Tight bound only (a loose bound earns nothing). If asked, argue Ω as well (half the operations cost at least …).

## 8. Exam-room rules

Front of the page only · only as many examples as asked · show the array/table **after each step** for traces ·
indices 0-based unless the question says "position" · re-read each prompt against your answer for missed sub-parts ·
budget ≈ 0.65 min per point.
