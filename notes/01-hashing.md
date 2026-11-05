# 01 - Hashing (Textbook 5.1-5.6, slides "Associative Arrays and Hashing", HW5)

> **Priority: very high.** The topics page says "anything from HWs, class or Ch 5-7 not on Exam 1" is fair game, and hashing is the only data structure on
> Exam 2 that is *entirely* new and that you can be asked to **trace by hand** (an insertion table for chaining / linear / quadratic / double hashing, usually with a
> collision or a rehash in it). Expect: (1) one table-filling trace, (2) one or two "explain / compare / why" questions (clustering, why prime, why lambda <= 0.5, lazy deletion),
> and (3) hash containers inside the cumulative **complexity-analysis and coding** questions (`unordered_set`/`unordered_map` average O(1), **worst O(n)** - always say both).
> The answers must use the **textbook** versions of everything (push_back into the chain, `f(i) = i*i`, `R - (x mod R)`, rehash at the textbook thresholds). Every trace in
> this file was produced with `python tools/study.py hash run ...`; re-run any of them to check yourself.

**Conventions used everywhere (textbook + professor, HW5 solutions):**

| Item | Rule |
|---|---|
| hash function | `hash(x) = x mod TableSize` for integer keys; strings use Fig 5.4 (Horner, 37) |
| probing | `h_i(x) = (hash(x) + f(i)) mod TableSize`, `i = 0, 1, 2, ...`, `f(0) = 0`. Linear `f(i) = i`; quadratic `f(i) = i*i`; double `f(i) = i * hash2(x)` |
| `hash2` | `hash2(x) = R - (x mod R)`, **R a prime smaller than TableSize** (HW5 uses **R = 7**). Never 0 (it is between 1 and R) |
| separate chaining | bucket `hash(x)` holds a list; check for the key first (duplicates are ignored), then **`push_back`** (new item goes at the END of the list). Fig 5.5's picture shows front-insertion; the code on p.200 and the HW solutions append |
| "cannot place" | a probing insert gives up after **TableSize probes** (HW5 5.1d: "Cannot place 1989") |
| rehash trigger | probing: after the insert, `++currentSize > TableSize/2` (integer division, i.e. lambda > 0.5). Chaining: `++currentSize > TableSize` (lambda > 1) |
| rehash result | new size `nextPrime(2 * oldSize)`, new hash `x mod newSize`; re-insert the old items **in old-index order** (chaining: bucket 0 front-to-back, then bucket 1, ...) |
| lazy deletion | `remove` marks the cell `DELETED`; `findPos` walks past DELETED cells; a plain insert goes to the first **EMPTY** cell it reaches; DELETED cells still count in `currentSize`. Exercise 5.7 reuses the first DELETED cell instead |
| table sizes in figures | the book's Figs 5.5, 5.11, 5.13, 5.18 and HW5 5.1 use size **10** "for convenience" (not prime). A real table is prime |

---

## 1. From arrays to hash tables (slides "Direct Address Tables", "Hash Functions")

### 1.1 Worked example first: a bit array is a set

The set {1, 3, 6, 8} over keys 0..8 stored with the **key itself as the array index**:

```
index:  0  1  2  3  4  5  6  7  8
value:  0  1  0  1  0  0  1  0  1        (1 = "present")
```

`contains(7)` = look at index 7 -> O(1). `insert(x)`, `remove(x)` = write index x -> O(1). That is a **direct address table**: O(1) insert, delete, lookup with *no collisions at all*.
The slide's second example uses the same idea with key-value pairs: key = quiz score 0..10, value = number of students with that score (index 3 holds 2, index 4 holds 4, ...).

### 1.2 Why it is rarely usable (slide "Limitations of direct addressing")

- Keys must be non-negative integers.
- The array must have one cell for **every possible key**, so you must know the maximum key. 9-digit ID numbers would need 10^9 cells for a class of 30 students.
- So it is almost never a reasonably sized array.

### 1.3 The fix: a hash function

A **hash function** `h(x)` maps keys of any size/type into `0 .. TableSize-1`. That solves the size problem but creates new ones (slide "Hash Functions"):

1. **Collisions** - two different keys with the same `h(x)`.
2. **Load factor** - lambda = (number of elements) / TableSize.
3. **Patterns in the data** that make many keys land in the same cell.

If we manage those, insert/delete/lookup are O(1) **on average** (not worst case - see section 9).

**Hash table vs hash map (slide):** "hash table" = just values (a set); "hash map" = key/value pairs. The book's Fig 5.1 is a map (`john 25000`), the rest of the chapter stores values only. `unordered_set` = hash table, `unordered_map` = hash map.

### Check yourself
1. Why can a direct address table not store the keys {5, 1000000}? Why is a hash table fine for it?
2. What three new problems does a hash function introduce?

<details><summary>Answer</summary>

1. The array needs a cell for every possible key up to the maximum (1,000,001 cells for two keys). A hash function maps both keys into a small table (e.g. size 11), at the price of possible collisions.
2. Collisions, the load factor (how full the table is), and data patterns that cause many keys to hash to the same place.
</details>

---

## 2. Hash functions (textbook 5.2, HW5 Part 2a)

### 2.1 Integers: `x mod TableSize`

Simple, fast, and spreads random integers evenly **if TableSize is prime**. Why prime: if the table size is 10 and all keys end in 0, every key lands in cell 0.

Engine: `python tools/study.py hash run 10,20,30,40,50,60 --size 10 --method chain`

- insert 10: hash = 10 mod 10 = 0 -> appended to bucket 0's list
- insert 20: hash = 20 mod 10 = 0 -> appended to bucket 0's list
- insert 30: hash = 30 mod 10 = 0 -> appended to bucket 0's list
- insert 40: hash = 40 mod 10 = 0 -> appended to bucket 0's list
- insert 50: hash = 50 mod 10 = 0 -> appended to bucket 0's list
- insert 60: hash = 60 mod 10 = 0 -> appended to bucket 0's list

Final table (bucket index above, list below):

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| 10 → 20 → 30 → 40 → 50 → 60 | – | – | – | – | – | – | – | – | – |

Same keys, **prime** size 11:

Engine: `python tools/study.py hash run 10,20,30,40,50,60 --size 11 --method chain`

- insert 10: hash = 10 mod 11 = 10 -> appended to bucket 10's list
- insert 20: hash = 20 mod 11 = 9 -> appended to bucket 9's list
- insert 30: hash = 30 mod 11 = 8 -> appended to bucket 8's list
- insert 40: hash = 40 mod 11 = 7 -> appended to bucket 7's list
- insert 50: hash = 50 mod 11 = 6 -> appended to bucket 6's list
- insert 60: hash = 60 mod 11 = 5 -> appended to bucket 5's list

Final table (bucket index above, list below):

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| – | – | – | – | – | 60 | 50 | 40 | 30 | 20 | 10 |

(The book, p.194: "it is often a good idea to ensure that the table size is prime." Prime sizes matter even more for quadratic probing and double hashing - section 4.)

### 2.2 Strings: the three functions of Figs 5.2-5.4 (p.195)

```cpp
// Fig 5.2 - add up the characters
int hash( const string & key, int tableSize )
{
    int hashVal = 0;
    for( char ch : key )
        hashVal += ch;
    return hashVal % tableSize;
}

// Fig 5.3 - only the first three characters ("not too good")
int hash( const string & key, int tableSize )
{
    return ( key[ 0 ] + 27 * key[ 1 ] + 729 * key[ 2 ] ) % tableSize;
}

// Fig 5.4 - all characters, Horner's rule with 37 ("good")
unsigned int hash( const string & key, int tableSize )
{
    unsigned int hashVal = 0;
    for( char ch : key )
        hashVal = 37 * hashVal + ch;
    return hashVal % tableSize;
}
```

**Worked example first.** The ASCII codes are a=97, c=99, t=116. Hash "cat", "act", "tac" (anagrams) and "cab" into a table of size 101:

| key | Fig 5.2 (sum) | Fig 5.3 (first 3 chars) | Fig 5.4 (Horner, 37) |
|---|---|---|---|
| "cat" | 312 mod 101 = **9** | 87282 mod 101 = **18** | 139236 mod 101 = **58** |
| "act" | 312 mod 101 = **9** | 87334 mod 101 = **70** | 136572 mod 101 = **20** |
| "tac" | 312 mod 101 = **9** | 74906 mod 101 = **65** | 162492 mod 101 = **84** |
| "cab" | 294 mod 101 = **92** | 74160 mod 101 = **26** | 139218 mod 101 = **40** |

- Fig 5.2 gives **the same value for every anagram** (the sum of the letters does not depend on order), so "cat", "act", "tac" collide.
- Fig 5.3 separates them (position matters) - but only looks at 3 characters: "cattle" and "catalog" would collide.
- Fig 5.4 uses every character and its position.

Horner's rule: the sum `key[n-1]*37^0 + key[n-2]*37^1 + ... + key[0]*37^(n-1)` is computed as `((k0*37 + k1)*37 + k2)...`: one multiply and one add per character, O(length). Overflow of `unsigned int` is allowed and harmless (it wraps); `unsigned` avoids a negative index.

### 2.3 HW5 Part 2a - pros and cons (professor's answer, paraphrased)

| function | pro | con |
|---|---|---|
| **Fig 5.2** (sum of chars) | simple, usually fine | non-uniform when strings are **short and the table is large** (values only reach 127 * length; book: for `TableSize` = 10,007 and keys of at most 8 chars only 0..1016 are reachable) or when the strings are **similar** (all anagrams collide) |
| **Fig 5.3** (first 3 chars) | **fastest** - O(1), does not depend on the string length | very prone to collisions: all strings with the same first 3 characters share a bucket (common prefixes = worst case). English has only 2,851 of 17,576 possible 3-letter combos, so ~28% of a big table is reachable |
| **Fig 5.4** (all chars, 37) | spreads even similar strings; "good" | **most expensive** - O(length) per hash; weak only if strings have equal length and differ in the last few characters. Very long keys: use only some characters (book p.196) |

Typical exam phrasing: "State one advantage and one disadvantage of each." Memorize the table above.

### Check yourself
1. Which of the three gives the same value for "stop", "pots", "tops"? Which is O(1) in the string length?
2. Table size 10,007, keys are at most 6 characters. How many different values can Fig 5.2 produce at most, and what fraction of the table is that?

<details><summary>Answer</summary>

1. Fig 5.2 (sum of characters; anagrams have the same sum). Fig 5.3 is O(1) in the length (looks at 3 characters).
2. At most 127 * 6 = 762 (values 0..762), i.e. 763 cells out of 10,007, about 7.6% of the table. The rest of the table can never be hit.
</details>

---

## 3. Separate chaining (textbook 5.3, HW5 5.1a and Part 2b)

### 3.1 Worked example first: HW5 5.1a

Input {4371, 1323, 6173, 4199, 4344, 9679, 1989}, `hash(x) = x mod 10`. Each bucket is a list; a new key is appended at the **end**.

Engine: `python tools/study.py hash run 4371,1323,6173,4199,4344,9679,1989 --size 10 --method chain`

- insert 4371: hash = 4371 mod 10 = 1 -> appended to bucket 1's list
- insert 1323: hash = 1323 mod 10 = 3 -> appended to bucket 3's list
- insert 6173: hash = 6173 mod 10 = 3 -> appended to bucket 3's list
- insert 4199: hash = 4199 mod 10 = 9 -> appended to bucket 9's list
- insert 4344: hash = 4344 mod 10 = 4 -> appended to bucket 4's list
- insert 9679: hash = 9679 mod 10 = 9 -> appended to bucket 9's list
- insert 1989: hash = 1989 mod 10 = 9 -> appended to bucket 9's list

Final table (bucket index above, list below):

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| – | 4371 | – | 1323 → 6173 | 4344 | – | – | – | – | 4199 → 9679 → 1989 |

The same thing as the HW's "table after each insertion" (like textbook 5.4), each column is the table after that insertion:

Table after each insertion (this is the layout the HW asks for, like textbook 5.4):

| cell | Start | ins 4371 | ins 1323 | ins 6173 | ins 4199 | ins 4344 | ins 9679 | ins 1989 |
|---|---|---|---|---|---|---|---|---|
| 0 |  |  |  |  |  |  |  |  |
| 1 |  | 4371 | 4371 | 4371 | 4371 | 4371 | 4371 | 4371 |
| 2 |  |  |  |  |  |  |  |  |
| 3 |  |  | 1323 | 1323 → 6173 | 1323 → 6173 | 1323 → 6173 | 1323 → 6173 | 1323 → 6173 |
| 4 |  |  |  |  |  | 4344 | 4344 | 4344 |
| 5 |  |  |  |  |  |  |  |  |
| 6 |  |  |  |  |  |  |  |  |
| 7 |  |  |  |  |  |  |  |  |
| 8 |  |  |  |  |  |  |  |  |
| 9 |  |  |  |  | 4199 | 4199 | 4199 → 9679 | 4199 → 9679 → 1989 |

Collisions here: 6173 (behind 1323 in bucket 3), 9679 and 1989 (behind 4199 in bucket 9). Note the lists have length 1, 2, 1, 3; the load factor is 7/10 = 0.7 and the average list length is 0.7.

Book's Fig 5.5: the first 10 perfect squares, size 10 (lambda = 1):

Engine: `python tools/study.py hash run 0,1,4,9,16,25,36,49,64,81 --size 10 --method chain`

- insert 0: hash = 0 mod 10 = 0 -> appended to bucket 0's list
- insert 1: hash = 1 mod 10 = 1 -> appended to bucket 1's list
- insert 4: hash = 4 mod 10 = 4 -> appended to bucket 4's list
- insert 9: hash = 9 mod 10 = 9 -> appended to bucket 9's list
- insert 16: hash = 16 mod 10 = 6 -> appended to bucket 6's list
- insert 25: hash = 25 mod 10 = 5 -> appended to bucket 5's list
- insert 36: hash = 36 mod 10 = 6 -> appended to bucket 6's list
- insert 49: hash = 49 mod 10 = 9 -> appended to bucket 9's list
- insert 64: hash = 64 mod 10 = 4 -> appended to bucket 4's list
- insert 81: hash = 81 mod 10 = 1 -> appended to bucket 1's list

Final table (bucket index above, list below):

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 1 → 81 | – | – | 4 → 64 | 25 | 16 → 36 | – | – | 9 → 49 |

(Fig 5.5 draws `81 -> 1` in bucket 1, i.e. it inserted at the front; the book code and the HW insert at the end. On the exam: **append at the end** unless told otherwise.)

### 3.2 The rule

- The table is a `vector<list<HashedObj>>`; element x lives in list number `myhash(x)`.
- **load factor** lambda = N / TableSize = average list length.
- Unsuccessful search: lambda nodes examined on average. **Successful search: about 1 + lambda/2** nodes (the matching node, plus on average half of the lambda other nodes in the list).
- So **the table size does not matter, the load factor does**. Rule: make the table about as large as the number of elements (lambda <= 1) - the code rehashes when lambda > 1.
- Lists can be replaced by anything (a BST, another hash table), but "we expect all lists to be short", so plain lists.
- Keys must supply `operator==` and a hash function (section 8).

### 3.3 The textbook code (Figs 5.6-5.10, pp.197-200) - HW5 Part 2b: explain every line

Class skeleton and `myhash` (Figs 5.6-5.7):

```cpp
template <typename HashedObj>
class HashTable
{
  public:
    explicit HashTable( int size = 101 );
    bool contains( const HashedObj & x ) const;
    void makeEmpty( );
    bool insert( const HashedObj & x );
    bool insert( HashedObj && x );
    bool remove( const HashedObj & x );

  private:
    vector<list<HashedObj>> theLists;   // The array of Lists
    int currentSize;
    void rehash( );
    size_t myhash( const HashedObj & x ) const;
};

size_t myhash( const HashedObj & x ) const
{
    static hash<HashedObj> hf;
    return hf( x ) % theLists.size( );
}
```

`theLists` is the table (one list per bucket); `currentSize` counts elements (not buckets); `myhash` runs the key through the `hash<>` function object (which returns a big `size_t`) and then reduces it into `0 .. TableSize-1` with `%`. `static` means the functor object is built once.

**Fig 5.9 - makeEmpty, contains, remove (p.200):**

```cpp
 1  void makeEmpty( )
 2  {
 3     for( auto & thisList : theLists )
 4        thisList.clear( );
 5  }
 6
 7  bool contains( const HashedObj & x ) const
 8  {
 9     auto & whichList = theLists[ myhash( x ) ];
10     return find( begin( whichList ), end( whichList ), x ) != end( whichList );
11  }
12
13  bool remove( const HashedObj & x )
14  {
15     auto & whichList = theLists[ myhash( x ) ];
16     auto itr = find( begin( whichList ), end( whichList ), x );
17
18     if( itr == end( whichList ) )
19        return false;
20
21     whichList.erase( itr );
22     --currentSize;
23     return true;
24  }
```

| line | what it does |
|---|---|
| 3-4 | range-for over every list **by reference** (`auto &`, so the real list is cleared, not a copy) and `clear()` it. Cost O(TableSize + N). As printed, this version does **not** reset `currentSize` |
| 9 | `myhash(x)` gives the bucket index; `theLists[...]` is that bucket's list; `auto &` binds a reference (no copy of the list - copying would be O(list length) and wrong for `remove`). `const` is allowed because we only read it |
| 10 | `std::find` scans the list from `begin` to `end` using `operator==`; if it reaches `end` the item was not there. Returns true iff found. Cost O(list length) = O(lambda) average, O(N) worst |
| 15 | same bucket lookup as line 9 (this time non-const, since we will modify the list) |
| 16 | search the list; `itr` points at x or equals `end(whichList)` |
| 18-19 | not found: nothing to remove, report failure with `false` |
| 21 | `list::erase(itr)` unlinks that node in O(1) (known position in a doubly linked list) |
| 22 | one fewer element - **`--currentSize`** (probing tables do *not* do this on remove, see section 5) |
| 23 | report success |

**Fig 5.10 - insert (p.200):**

```cpp
 1  bool insert( const HashedObj & x )
 2  {
 3     auto & whichList = theLists[ myhash( x ) ];
 4     if( find( begin( whichList ), end( whichList ), x ) != end( whichList ) )
 5        return false;
 6     whichList.push_back( x );
 7
 8     // Rehash; see Section 5.5
 9     if( ++currentSize > theLists.size( ) )
10        rehash( );
11
12     return true;
13  }
```

| line | what it does |
|---|---|
| 3 | pick the bucket by reference |
| 4-5 | the table is a set: if x is already in the list, do nothing and return `false` (no duplicates; the book remarks that a count member could be kept instead) |
| 6 | x is new: **append at the end** (the book says the element can go anywhere; push_back is most convenient here) |
| 9-10 | increment the element count *first*, then compare with the table size: if `currentSize > TableSize` (lambda > 1) call `rehash()` (section 6). Note the order: `++` happens before the comparison, so with TableSize 5 the rehash triggers on the **6th** insert |
| 12 | insertion succeeded |

### 3.4 Chaining with a rehash

Engine: `python tools/study.py hash run 10,15,20,7,12,25,3,8 --size 5 --method chain --rehash`

- insert 10: hash = 10 mod 5 = 0 -> appended to bucket 0's list
- insert 15: hash = 15 mod 5 = 0 -> appended to bucket 0's list
- insert 20: hash = 20 mod 5 = 0 -> appended to bucket 0's list
- insert 7: hash = 7 mod 5 = 2 -> appended to bucket 2's list
- insert 12: hash = 12 mod 5 = 2 -> appended to bucket 2's list
- insert 25: hash = 25 mod 5 = 0 -> appended to bucket 0's list
  - *load factor 6/5 > 1 -> rehash*
  - *REHASH: new TableSize = nextPrime(2*5) = 11; re-inserting [10, 15, 20, 25, 7, 12] in old-table order with hash = x mod 11*
- insert 10: hash = 10 mod 11 = 10 -> appended to bucket 10's list
- insert 15: hash = 15 mod 11 = 4 -> appended to bucket 4's list
- insert 20: hash = 20 mod 11 = 9 -> appended to bucket 9's list
- insert 25: hash = 25 mod 11 = 3 -> appended to bucket 3's list
- insert 7: hash = 7 mod 11 = 7 -> appended to bucket 7's list
- insert 12: hash = 12 mod 11 = 1 -> appended to bucket 1's list
- insert 3: hash = 3 mod 11 = 3 -> appended to bucket 3's list
- insert 8: hash = 8 mod 11 = 8 -> appended to bucket 8's list

Final table (final TableSize 11) (bucket index above, list below):

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| – | 12 | – | 25 → 3 | 15 | – | – | 7 | 8 | 20 | 10 |

The 6th insertion makes `currentSize = 6 > 5`, so the table is rebuilt at `nextPrime(10) = 11` and the six items are re-inserted bucket by bucket (bucket 0: 10, 15, 20, 25; bucket 2: 7, 12) using `x mod 11`.

### Check yourself
1. Table size 7 (chaining, no rehash), insert 8, 15, 22, 5, 12 in that order. Write bucket 1 and bucket 5.
2. What is the expected number of nodes examined in a *successful* search at lambda = 2?
3. In `remove` (Fig 5.9) why is `whichList` a reference?

<details><summary>Answer</summary>

1. 8 mod 7 = 1, 15 mod 7 = 1, 22 mod 7 = 1, 5, 12 mod 7 = 5. Bucket 1: 8 -> 15 -> 22 (insertion order, append at end). Bucket 5: 5 -> 12.
2. 1 + lambda/2 = 2 nodes (and an unsuccessful search examines lambda = 2 on average).
3. So that `erase` modifies the real list stored in the table. A by-value copy would be O(length) and the removal would happen on the copy and be lost.
</details>

---

## 4. Probing hash tables (textbook 5.4: "hash tables without linked lists")

All data lives **inside the array**. When x collides, try cells `h_0(x), h_1(x), h_2(x), ...` where `h_i(x) = (hash(x) + f(i)) mod TableSize` and `f(0) = 0`; take the first EMPTY one. Because everything is inside the table, a bigger table is needed than for chaining: **keep lambda below 0.5**. Probing tables are also called *open addressing* / *closed hashing* (the slides say closed hashing needs a lower load factor than open hashing = chaining).

### 4.1 Linear probing, `f(i) = i`

**Worked example first (Fig 5.11):** insert 89, 18, 49, 58, 69, size 10.

Table after each insertion (this is the layout the HW asks for, like textbook 5.4):

| cell | Start | ins 89 | ins 18 | ins 49 | ins 58 | ins 69 |
|---|---|---|---|---|---|---|
| 0 |  |  |  | 49 | 49 | 49 |
| 1 |  |  |  |  | 58 | 58 |
| 2 |  |  |  |  |  | 69 |
| 3 |  |  |  |  |  |  |
| 4 |  |  |  |  |  |  |
| 5 |  |  |  |  |  |  |
| 6 |  |  |  |  |  |  |
| 7 |  |  |  |  |  |  |
| 8 |  |  | 18 | 18 | 18 | 18 |
| 9 |  | 89 | 89 | 89 | 89 | 89 |

Engine: `python tools/study.py hash run 89,18,49,58,69 --size 10 --method linear`

- insert 89: hash = 89 mod 10 = 9 -> placed at 9
- insert 18: hash = 18 mod 10 = 8 -> placed at 8
- insert 49: hash = 49 mod 10 = 9; collisions at 9; tried h0=9, h1=0 -> placed at 0
- insert 58: hash = 58 mod 10 = 8; collisions at 8, 9, 0; tried h0=8, h1=9, h2=0, h3=1 -> placed at 1
- insert 69: hash = 69 mod 10 = 9; collisions at 9, 0, 1; tried h0=9, h1=0, h2=1, h3=2 -> placed at 2

Final table (cell index above, content below; `–` = empty, `DEL` = deleted):

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| 49 | 58 | 69 | – | – | – | – | – | 18 | 89 |

How to do it by hand: compute `x mod 10`; if that cell is taken look at the next one (wrap from 9 to 0), and so on. 58 starts at 8 and has to try 8, 9, 0, 1 (three collisions) - the occupied block 8,9,0 is a **cluster**.

**Primary clustering:** blocks of occupied cells form even when the table is mostly empty; any key that hashes *into* the block must walk to its end and then *makes the block longer*. Keys with different home cells share the same probe path (here 89, 49, 58, 69 all end up walking over each other).

**HW5 5.1b** - the same input as 5.1a, linear probing, size 10:

Table after each insertion (this is the layout the HW asks for, like textbook 5.4):

| cell | Start | ins 4371 | ins 1323 | ins 6173 | ins 4199 | ins 4344 | ins 9679 | ins 1989 |
|---|---|---|---|---|---|---|---|---|
| 0 |  |  |  |  |  |  | 9679 | 9679 |
| 1 |  | 4371 | 4371 | 4371 | 4371 | 4371 | 4371 | 4371 |
| 2 |  |  |  |  |  |  |  | 1989 |
| 3 |  |  | 1323 | 1323 | 1323 | 1323 | 1323 | 1323 |
| 4 |  |  |  | 6173 | 6173 | 6173 | 6173 | 6173 |
| 5 |  |  |  |  |  | 4344 | 4344 | 4344 |
| 6 |  |  |  |  |  |  |  |  |
| 7 |  |  |  |  |  |  |  |  |
| 8 |  |  |  |  |  |  |  |  |
| 9 |  |  |  |  | 4199 | 4199 | 4199 | 4199 |

Engine: `python tools/study.py hash run 4371,1323,6173,4199,4344,9679,1989 --size 10 --method linear`

- insert 4371: hash = 4371 mod 10 = 1 -> placed at 1
- insert 1323: hash = 1323 mod 10 = 3 -> placed at 3
- insert 6173: hash = 6173 mod 10 = 3; collisions at 3; tried h0=3, h1=4 -> placed at 4
- insert 4199: hash = 4199 mod 10 = 9 -> placed at 9
- insert 4344: hash = 4344 mod 10 = 4; collisions at 4; tried h0=4, h1=5 -> placed at 5
- insert 9679: hash = 9679 mod 10 = 9; collisions at 9; tried h0=9, h1=0 -> placed at 0
- insert 1989: hash = 1989 mod 10 = 9; collisions at 9, 0, 1; tried h0=9, h1=0, h2=1, h3=2 -> placed at 2

Final table (cell index above, content below; `–` = empty, `DEL` = deleted):

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| 9679 | 4371 | 1989 | 1323 | 6173 | 4344 | – | – | – | 4199 |

Look at what happened: 6173 (home 3) landed at 4; 4344 (home 4) was *pushed* to 5 because 6173 took its home cell - a collision between keys with **different** hash values. 9679 wrapped around to 0; 1989 (home 9) walked 9, 0, 1 and finally took 2. That is primary clustering in action. Your answer table should match the professor's: `0:9679 1:4371 2:1989 3:1323 4:6173 5:4344 9:4199`.

### 4.2 Quadratic probing, `f(i) = i*i`

Probe sequence from home h: `h, h+1, h+4, h+9, h+16, ...` (mod TableSize).

**Worked example first (Fig 5.13):** same input, size 10.

Table after each insertion (this is the layout the HW asks for, like textbook 5.4):

| cell | Start | ins 89 | ins 18 | ins 49 | ins 58 | ins 69 |
|---|---|---|---|---|---|---|
| 0 |  |  |  | 49 | 49 | 49 |
| 1 |  |  |  |  |  |  |
| 2 |  |  |  |  | 58 | 58 |
| 3 |  |  |  |  |  | 69 |
| 4 |  |  |  |  |  |  |
| 5 |  |  |  |  |  |  |
| 6 |  |  |  |  |  |  |
| 7 |  |  |  |  |  |  |
| 8 |  |  | 18 | 18 | 18 | 18 |
| 9 |  | 89 | 89 | 89 | 89 | 89 |

Engine: `python tools/study.py hash run 89,18,49,58,69 --size 10 --method quadratic`

- insert 89: hash = 89 mod 10 = 9 -> placed at 9
- insert 18: hash = 18 mod 10 = 8 -> placed at 8
- insert 49: hash = 49 mod 10 = 9; collisions at 9; tried h0=9, h1=0 -> placed at 0
- insert 58: hash = 58 mod 10 = 8; collisions at 8, 9; tried h0=8, h1=9, h2=2 -> placed at 2
- insert 69: hash = 69 mod 10 = 9; collisions at 9, 0; tried h0=9, h1=0, h2=3 -> placed at 3

Final table (cell index above, content below; `–` = empty, `DEL` = deleted):

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| 49 | – | 58 | 69 | – | – | – | – | 18 | 89 |

58: home 8 taken, 8+1 = 9 taken, 8+4 = 12 -> 2. 69: home 9 taken, 9+1 = 10 -> 0 taken, 9+4 = 13 -> 3. Compare with linear: the keys are spread out instead of forming one block - **no primary clustering**.

**HW5 5.1c:**

Table after each insertion (this is the layout the HW asks for, like textbook 5.4):

| cell | Start | ins 4371 | ins 1323 | ins 6173 | ins 4199 | ins 4344 | ins 9679 | ins 1989 |
|---|---|---|---|---|---|---|---|---|
| 0 |  |  |  |  |  |  | 9679 | 9679 |
| 1 |  | 4371 | 4371 | 4371 | 4371 | 4371 | 4371 | 4371 |
| 2 |  |  |  |  |  |  |  |  |
| 3 |  |  | 1323 | 1323 | 1323 | 1323 | 1323 | 1323 |
| 4 |  |  |  | 6173 | 6173 | 6173 | 6173 | 6173 |
| 5 |  |  |  |  |  | 4344 | 4344 | 4344 |
| 6 |  |  |  |  |  |  |  |  |
| 7 |  |  |  |  |  |  |  |  |
| 8 |  |  |  |  |  |  |  | 1989 |
| 9 |  |  |  |  | 4199 | 4199 | 4199 | 4199 |

Engine: `python tools/study.py hash run 4371,1323,6173,4199,4344,9679,1989 --size 10 --method quadratic`

- insert 4371: hash = 4371 mod 10 = 1 -> placed at 1
- insert 1323: hash = 1323 mod 10 = 3 -> placed at 3
- insert 6173: hash = 6173 mod 10 = 3; collisions at 3; tried h0=3, h1=4 -> placed at 4
- insert 4199: hash = 4199 mod 10 = 9 -> placed at 9
- insert 4344: hash = 4344 mod 10 = 4; collisions at 4; tried h0=4, h1=5 -> placed at 5
- insert 9679: hash = 9679 mod 10 = 9; collisions at 9; tried h0=9, h1=0 -> placed at 0
- insert 1989: hash = 1989 mod 10 = 9; collisions at 9, 0, 3; tried h0=9, h1=0, h2=3, h3=8 -> placed at 8

Final table (cell index above, content below; `–` = empty, `DEL` = deleted):

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| 9679 | 4371 | – | 1323 | 6173 | 4344 | – | – | 1989 | 4199 |

1989: home 9 (taken), 9+1 = 10 -> 0 (taken by 9679), 9+4 = 13 -> 3 (taken by 1323), 9+9 = 18 -> 8 empty -> placed at 8. This matches the HW5 official table (`8: 1989`).

**Secondary clustering.** Keys with the *same home cell* follow the *same probe sequence*, so they pile up along it. Five keys that all have home 5 in a table of size 13:

Engine: `python tools/study.py hash run 18,31,44,5,57 --size 13 --method quadratic`

- insert 18: hash = 18 mod 13 = 5 -> placed at 5
- insert 31: hash = 31 mod 13 = 5; collisions at 5; tried h0=5, h1=6 -> placed at 6
- insert 44: hash = 44 mod 13 = 5; collisions at 5, 6; tried h0=5, h1=6, h2=9 -> placed at 9
- insert 5: hash = 5 mod 13 = 5; collisions at 5, 6, 9; tried h0=5, h1=6, h2=9, h3=1 -> placed at 1
- insert 57: hash = 57 mod 13 = 5; collisions at 5, 6, 9, 1; tried h0=5, h1=6, h2=9, h3=1, h4=8 -> placed at 8

Final table (cell index above, content below; `–` = empty, `DEL` = deleted):

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| – | 5 | – | – | – | 18 | 31 | – | 57 | 44 | – | – | – |

Each new key re-walks 5, 6, 9, 1, ... Compare double hashing on the same keys (section 4.4), where the sequence depends on the key, not only on the home cell. The book says secondary clustering "generally causes less than an extra half probe per search": a slight theoretical blemish.

**The fast way to compute the next probe (Fig 5.16, p.206)** - no multiplication needed, because `f(i) = f(i-1) + 2i - 1`:

```cpp
int findPos( const HashedObj & x ) const
{
    int offset = 1;
    int currentPos = myhash( x );

    while( array[ currentPos ].info != EMPTY &&
           array[ currentPos ].element != x )
    {
        currentPos += offset;            // Compute ith probe
        offset += 2;
        if( currentPos >= array.size( ) )
            currentPos -= array.size( );
    }
    return currentPos;
}
```

Line by line: `offset` starts at 1 = 1^2 - 0^2. Start at the home cell. The `while` keeps going while the cell is **not EMPTY and does not hold x** (so it stops at an EMPTY cell *or* at the cell containing x - a DELETED cell that holds some other key does **not** stop it; section 5). Each step moves ahead by `offset` (1, then 3, then 5, 7, ...), because 1 + 3 + 5 + ... + (2i-1) = i^2, so the i-th probe is `home + i^2`. Wrap-around is a single subtraction, not a modulo (enough because the loop ends within about TableSize/2 probes, so `offset` stays below TableSize). The book's warning: *the order of the two tests matters, do not switch it* - test `info != EMPTY` first so we never compare against the (meaningless) element of an empty cell.

Probe positions for home 5, size 13: 5, 5+1 = 6, 6+3 = 9, 9+5 = 14 -> 1, 1+7 = 8: exactly the cells 5, 6, 9, 1, 8 in the trace above.

### 4.3 Theorem 5.1 and why quadratic probing needs prime size and lambda <= 0.5

> **Theorem 5.1.** If quadratic probing is used and the table size is **prime**, then a new element can always be inserted if the table is **at least half empty**.

Proof idea (be able to reproduce): let TableSize = p be an odd prime. Take two probes `h + i^2` and `h + j^2` with `0 <= i, j <= floor(p/2)` and suppose they land on the same cell with `i != j`. Then `i^2 = j^2 (mod p)`, so `(i - j)(i + j) = 0 (mod p)`. Because p is prime, p divides `(i - j)` or `(i + j)`. But `0 < |i - j| < p` (i and j are distinct and at most p/2) and `0 < i + j < p` (both at most p/2 and not both 0), so neither is divisible by p: **contradiction**. Hence the first `floor(p/2) + 1` probes (i = 0 .. floor(p/2)) hit **distinct cells**; more than half the table is therefore available as alternatives, and if at most `floor(p/2)` cells are occupied one of those cells must be empty.

Consequences:
- Table **more than half full** -> no guarantee. Even *one more than half* full, an insertion can fail (unlikely but possible).
- Table size **not prime** -> far fewer alternative cells. Book example: size 16 reaches only distances 1, 4, 9.
- (Footnote: a prime of the form 4k+3 with `f(i) = +-i^2` probes the whole table.)

Demonstration, size 16, all keys ≡ 0 (mod 16), table nearly empty:

Engine: `python tools/study.py hash run 16,32,48,64,80 --size 16 --method quadratic`

- insert 16: hash = 16 mod 16 = 0 -> placed at 0
- insert 32: hash = 32 mod 16 = 0; collisions at 0; tried h0=0, h1=1 -> placed at 1
- insert 48: hash = 48 mod 16 = 0; collisions at 0, 1; tried h0=0, h1=1, h2=4 -> placed at 4
- insert 64: hash = 64 mod 16 = 0; collisions at 0, 1, 4; tried h0=0, h1=1, h2=4, h3=9 -> placed at 9
- insert 80: home 0; probed 0, 1, 4, 9, 0, 9, 4, 1, 0, 1, 4, 9, 0, 9, 4, 1 - all occupied -> CANNOT PLACE 80

Final table (cell index above, content below; `–` = empty, `DEL` = deleted):

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 16 | 32 | – | – | 48 | – | – | – | – | 64 | – | – | – | – | – | – |

Only cells 0, 1, 4, 9 are ever probed (0, 1, 4, 9, then 16 -> 0, 25 -> 9, 36 -> 4, 49 -> 1, ...), so the fifth key cannot be placed although 12 cells are empty.

Demonstration, **prime** size but lambda too high (size 11, 7 keys already in, lambda = 0.64 > 0.5):

Engine: `python tools/study.py hash run 54,23,41,67,32,10,98,21 --size 11 --method quadratic`

- insert 54: hash = 54 mod 11 = 10 -> placed at 10
- insert 23: hash = 23 mod 11 = 1 -> placed at 1
- insert 41: hash = 41 mod 11 = 8 -> placed at 8
- insert 67: hash = 67 mod 11 = 1; collisions at 1; tried h0=1, h1=2 -> placed at 2
- insert 32: hash = 32 mod 11 = 10; collisions at 10; tried h0=10, h1=0 -> placed at 0
- insert 10: hash = 10 mod 11 = 10; collisions at 10, 0; tried h0=10, h1=0, h2=3 -> placed at 3
- insert 98: hash = 98 mod 11 = 10; collisions at 10, 0, 3, 8; tried h0=10, h1=0, h2=3, h3=8, h4=4 -> placed at 4
- insert 21: home 10; probed 10, 0, 3, 8, 4, 2, 2, 4, 8, 3, 0 - all occupied -> CANNOT PLACE 21

Final table (cell index above, content below; `–` = empty, `DEL` = deleted):

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| 32 | 23 | 67 | 10 | 98 | – | – | – | 41 | – | 54 |

21 (home 10) probes 10, 0, 3, 8, 4, 2, then 2, 4, 8, 3, 0 again: only six distinct cells, all occupied; cells 5, 6, 7, 9 are empty but never examined. The engine reports **CANNOT PLACE 21** after TableSize probes. This is exactly why the book rehashes when the table is half full.

### 4.4 Double hashing, `f(i) = i * hash2(x)`

`hash2(x) = R - (x mod R)` with R prime < TableSize. Probe sequence: `h, h + hash2, h + 2*hash2, ...` mod TableSize. The step depends on the key, so keys with the same home usually diverge - this removes secondary clustering. `hash2` must **never be 0** (it would never move), and the table size must be prime so that every step size cycles through all cells.

**Worked example first (Fig 5.18, R = 7):**

Table after each insertion (this is the layout the HW asks for, like textbook 5.4):

| cell | Start | ins 89 | ins 18 | ins 49 | ins 58 | ins 69 |
|---|---|---|---|---|---|---|
| 0 |  |  |  |  |  | 69 |
| 1 |  |  |  |  |  |  |
| 2 |  |  |  |  |  |  |
| 3 |  |  |  |  | 58 | 58 |
| 4 |  |  |  |  |  |  |
| 5 |  |  |  |  |  |  |
| 6 |  |  |  | 49 | 49 | 49 |
| 7 |  |  |  |  |  |  |
| 8 |  |  | 18 | 18 | 18 | 18 |
| 9 |  | 89 | 89 | 89 | 89 | 89 |

Engine: `python tools/study.py hash run 89,18,49,58,69 --size 10 --method double --R 7`

- insert 89: hash = 89 mod 10 = 9 -> placed at 9
- insert 18: hash = 18 mod 10 = 8 -> placed at 8
- insert 49: hash = 49 mod 10 = 9; hash2 = 7 - (49 mod 7) = 7; collisions at 9; tried h0=9, h1=6 -> placed at 6
- insert 58: hash = 58 mod 10 = 8; hash2 = 7 - (58 mod 7) = 5; collisions at 8; tried h0=8, h1=3 -> placed at 3
- insert 69: hash = 69 mod 10 = 9; hash2 = 7 - (69 mod 7) = 1; collisions at 9; tried h0=9, h1=0 -> placed at 0

Final table (cell index above, content below; `–` = empty, `DEL` = deleted):

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| 69 | – | – | 58 | – | – | 49 | – | 18 | 89 |

- 49: home 9 taken. hash2(49) = 7 - (49 mod 7) = 7 - 0 = **7**. Next cell 9 + 7 = 16 mod 10 = 6.
- 58: home 8 taken. hash2(58) = 7 - (58 mod 7) = 7 - 2 = 5. 8 + 5 = 13 -> 3.
- 69: home 9 taken. hash2(69) = 7 - (69 mod 7) = 7 - 6 = 1. 9 + 1 = 10 -> 0.

(The book then says: inserting 60 (home 0) hits a collision; hash2(60) = 3 so try 3, 6, 9, then 2.) Check, and the non-prime failure the book describes - insert 23 (home 3 taken by 58, hash2(23) = 5, and with size 10 only cells 3 and 8 are ever reached):

Engine: `python tools/study.py hash run 89,18,49,58,69,23,60 --size 10 --method double --R 7`

- insert 89: hash = 89 mod 10 = 9 -> placed at 9
- insert 18: hash = 18 mod 10 = 8 -> placed at 8
- insert 49: hash = 49 mod 10 = 9; hash2 = 7 - (49 mod 7) = 7; collisions at 9; tried h0=9, h1=6 -> placed at 6
- insert 58: hash = 58 mod 10 = 8; hash2 = 7 - (58 mod 7) = 5; collisions at 8; tried h0=8, h1=3 -> placed at 3
- insert 69: hash = 69 mod 10 = 9; hash2 = 7 - (69 mod 7) = 1; collisions at 9; tried h0=9, h1=0 -> placed at 0
- insert 23: home 3; hash2(23) = 7 - (23 mod 7) = 5; probed 3, 8, 3, 8, 3, 8, 3, 8, 3, 8 - all occupied -> CANNOT PLACE 23
- insert 60: hash = 60 mod 10 = 0; hash2 = 7 - (60 mod 7) = 3; collisions at 0, 3, 6, 9; tried h0=0, h1=3, h2=6, h3=9, h4=2 -> placed at 2

Final table (cell index above, content below; `–` = empty, `DEL` = deleted):

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| 69 | – | 60 | 58 | – | – | 49 | – | 18 | 89 |

**HW5 5.1d** (R = 7, size 10):

Table after each insertion (this is the layout the HW asks for, like textbook 5.4):

| cell | Start | ins 4371 | ins 1323 | ins 6173 | ins 4199 | ins 4344 | ins 9679 | ins 1989 |
|---|---|---|---|---|---|---|---|---|
| 0 |  |  |  |  |  |  |  |  |
| 1 |  | 4371 | 4371 | 4371 | 4371 | 4371 | 4371 | 4371 |
| 2 |  |  |  |  |  |  |  |  |
| 3 |  |  | 1323 | 1323 | 1323 | 1323 | 1323 | 1323 |
| 4 |  |  |  | 6173 | 6173 | 6173 | 6173 | 6173 |
| 5 |  |  |  |  |  |  | 9679 | 9679 |
| 6 |  |  |  |  |  |  |  |  |
| 7 |  |  |  |  |  | 4344 | 4344 | 4344 |
| 8 |  |  |  |  |  |  |  |  |
| 9 |  |  |  |  | 4199 | 4199 | 4199 | 4199 |

Engine: `python tools/study.py hash run 4371,1323,6173,4199,4344,9679,1989 --size 10 --method double --R 7`

- insert 4371: hash = 4371 mod 10 = 1 -> placed at 1
- insert 1323: hash = 1323 mod 10 = 3 -> placed at 3
- insert 6173: hash = 6173 mod 10 = 3; hash2 = 7 - (6173 mod 7) = 1; collisions at 3; tried h0=3, h1=4 -> placed at 4
- insert 4199: hash = 4199 mod 10 = 9 -> placed at 9
- insert 4344: hash = 4344 mod 10 = 4; hash2 = 7 - (4344 mod 7) = 3; collisions at 4; tried h0=4, h1=7 -> placed at 7
- insert 9679: hash = 9679 mod 10 = 9; hash2 = 7 - (9679 mod 7) = 2; collisions at 9, 1, 3; tried h0=9, h1=1, h2=3, h3=5 -> placed at 5
- insert 1989: home 9; hash2(1989) = 7 - (1989 mod 7) = 6; probed 9, 5, 1, 7, 3, 9, 5, 1, 7, 3 - all occupied -> CANNOT PLACE 1989

Final table (cell index above, content below; `–` = empty, `DEL` = deleted):

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| – | 4371 | – | 1323 | 6173 | 9679 | – | 4344 | – | 4199 |

By hand for the last three: 4344: home 4 taken (6173). hash2 = 7 - (4344 mod 7) = 7 - 4 = 3 -> 7. 9679: home 9 taken (4199). hash2 = 7 - (9679 mod 7) = 7 - 5 = 2 -> 11 mod 10 = 1 (taken), 3 (taken), 5 -> placed at 5. 1989: home 9, hash2 = 7 - (1989 mod 7) = 7 - 1 = 6: 9, 15 -> 5, 11 -> 1, 7, 3, 9, ... only cells 9, 5, 1, 7, 3 (step 6 mod 10 is even, size 10 is not prime) -> all taken -> **"Cannot place 1989"** (the official HW5 note). Table: `1:4371 3:1323 4:6173 5:9679 7:4344 9:4199`.

Same keys in a table of 11 (prime) with R = 7 - everything fits:

Engine: `python tools/study.py hash run 4371,1323,6173,4199,4344,9679,1989 --size 11 --method double --R 7`

- insert 4371: hash = 4371 mod 11 = 4 -> placed at 4
- insert 1323: hash = 1323 mod 11 = 3 -> placed at 3
- insert 6173: hash = 6173 mod 11 = 2 -> placed at 2
- insert 4199: hash = 4199 mod 11 = 8 -> placed at 8
- insert 4344: hash = 4344 mod 11 = 10 -> placed at 10
- insert 9679: hash = 9679 mod 11 = 10; hash2 = 7 - (9679 mod 7) = 2; collisions at 10; tried h0=10, h1=1 -> placed at 1
- insert 1989: hash = 1989 mod 11 = 9 -> placed at 9

Final table (cell index above, content below; `–` = empty, `DEL` = deleted):

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| – | 9679 | 6173 | 1323 | 4371 | – | – | – | 4199 | 1989 | 4344 |

### 4.5 Three-way comparison on one input

Input 54, 23, 41, 67, 32, 10, 98, size 11, R = 7:

| method | final table (cell:key) |
|---|---|
| chaining | `1:[23,67] 8:[41] 10:[54,32,10,98]` |
| linear | `0:32 1:23 2:67 3:10 4:98 8:41 10:54` |
| quadratic | `0:32 1:23 2:67 3:10 4:98 8:41 10:54` |
| double (R=7) | `1:23 2:32 3:10 4:67 6:98 8:41 10:54` |

Linear: 10 (home 10) walks over 54, 32, 23, 67 and lands at 3 (the cluster 0-2 plus 10 grows). Quadratic: spreads over 0, 3, 4. Double: different step sizes send 32, 10, 98 to 2, 3, 6.

### Check yourself
1. Quadratic probing, size 13. Keys 6, 19, 32, 45 (all home 6). Where does each go?
2. Linear probing, size 8. Insert 16, 24, 8, 7, 15 (in order). Where does 15 go and how many probes does it take?
3. Double hashing, size 11, R = 5. 27 collides at home 5. What is hash2(27) and the second cell tried?
4. Name the type of clustering: (a) keys with different homes join one block; (b) keys with the same home follow one path.

<details><summary>Answer</summary>

1. insert 6: hash = 6 mod 13 = 6 → placed at 6; insert 19: hash = 19 mod 13 = 6; collisions at 6; tried h0=6, h1=7 → placed at 7; insert 32: hash = 32 mod 13 = 6; collisions at 6, 7; tried h0=6, h1=7, h2=10 → placed at 10; insert 45: hash = 45 mod 13 = 6; collisions at 6, 7, 10; tried h0=6, h1=7, h2=10, h3=2 → placed at 2
   Final: `2:45 6:6 7:19 10:32`
2. insert 15: hash = 15 mod 8 = 7; collisions at 7, 0, 1, 2; tried h0=7, h1=0, h2=1, h3=2, h4=3 -> placed at 3
   (5 probes: cells 7, 0, 1, 2, 3.) Final: `0:16 1:24 2:8 3:15 7:7`
3. hash2(27) = 5 - (27 mod 5) = 5 - 2 = 3; second cell = (5 + 3) mod 11 = 8. Engine: insert 27: hash = 27 mod 11 = 5; hash2 = 5 - (27 mod 5) = 3; collisions at 5; tried h0=5, h1=8 -> placed at 8
4. (a) primary clustering (linear probing); (b) secondary clustering (quadratic probing).
</details>

---

## 5. Deletion and lazy deletion (textbook 5.4.2, Fig 5.17; HW5 5.7b)

**Why standard deletion fails in a probing table:** removing a cell that an earlier collision walked *past* breaks the probe path of the keys behind it - they would hit the now-EMPTY cell and a `find` would stop too early ("if we remove 89, then virtually all the remaining find operations will fail"). So every cell has a state: `ACTIVE`, `EMPTY`, or `DELETED` (a tombstone).

```cpp
bool remove( const HashedObj & x )
{
    int currentPos = findPos( x );
    if( !isActive( currentPos ) )
        return false;

    array[ currentPos ].info = DELETED;
    return true;
}
```

`findPos` (Fig 5.16, above) walks the probe sequence; DELETED cells do **not** stop it (they are not EMPTY, and they hold a different element), so we continue past them. `contains(x) = isActive(findPos(x))`. Note: `remove` does **not** decrement `currentSize` - DELETED cells keep counting toward the half-full limit and are only dropped by the next rehash.

**Worked example first.** Linear probing, size 11. Insert 22, 33, 44, 55 (all home 0), then 12 (home 1), then remove 33, find 44, find 12, find 66 (not present), insert 66, find 66:

Engine: `python tools/study.py hash run 22,33,44,55,12,-33,?44,?12,?66,66,?66 --size 11 --method linear`

- insert 22: hash = 22 mod 11 = 0 -> placed at 0
- insert 33: hash = 33 mod 11 = 0; collisions at 0; tried h0=0, h1=1 -> placed at 1
- insert 44: hash = 44 mod 11 = 0; collisions at 0, 1; tried h0=0, h1=1, h2=2 -> placed at 2
- insert 55: hash = 55 mod 11 = 0; collisions at 0, 1, 2; tried h0=0, h1=1, h2=2, h3=3 -> placed at 3
- insert 12: hash = 12 mod 11 = 1; collisions at 1, 2, 3; tried h0=1, h1=2, h2=3, h3=4 -> placed at 4
- remove 33: probed 0, 1 -> found at 1, marked DELETED (lazy deletion)
- find 44: probed 0, 1, 2 -> found
- find 12: probed 1, 2, 3, 4 -> found
- find 66: probed 0, 1, 2, 3, 4, 5 -> not found
- insert 66: hash = 66 mod 11 = 0; collisions at 0, 1, 2, 3, 4; tried h0=0, h1=1, h2=2, h3=3, h4=4, h5=5 -> placed at 5
- find 66: probed 0, 1, 2, 3, 4, 5 -> found

Final table (cell index above, content below; `–` = empty, `DEL` = deleted):

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| 22 | DEL | 44 | 55 | 12 | 66 | – | – | – | – | – |

Observe: after removing 33 the cell 1 is DELETED. `find 44` still walks 0, 1 (deleted: skip, not stop), 2 -> found. `find 66` (absent) walks until the first EMPTY cell, 5. And with the textbook code, **`insert 66` also goes to cell 5, the first EMPTY cell** - the DELETED cell 1 is not reused, so the tombstone stays and `currentSize` grows.

**Exercise 5.7 variant** (the professor's preferred lazy deletion, "deleted locations are treated as empty when inserting and as occupied during a search"): insert at the **first inactive (EMPTY or DELETED) cell on the probe path**; `findPos` remembers it in an extra variable but still scans to the EMPTY/x cell to be sure x is not already there.

Engine: `python tools/study.py hash run 22,33,44,55,12,-33,?44,?12,?66,66,?66 --size 11 --method linear --reuse-deleted`

- insert 22: hash = 22 mod 11 = 0 -> placed at 0
- insert 33: hash = 33 mod 11 = 0; collisions at 0; tried h0=0, h1=1 -> placed at 1
- insert 44: hash = 44 mod 11 = 0; collisions at 0, 1; tried h0=0, h1=1, h2=2 -> placed at 2
- insert 55: hash = 55 mod 11 = 0; collisions at 0, 1, 2; tried h0=0, h1=1, h2=2, h3=3 -> placed at 3
- insert 12: hash = 12 mod 11 = 1; collisions at 1, 2, 3; tried h0=1, h1=2, h2=3, h3=4 -> placed at 4
- remove 33: probed 0, 1 -> found at 1, marked DELETED (lazy deletion)
- find 44: probed 0, 1, 2 -> found
- find 12: probed 1, 2, 3, 4 -> found
- find 66: probed 0, 1, 2, 3, 4, 5 -> not found
- insert 66: hash = 66 mod 11 = 0; collisions at 0; tried h0=0, h1=1 -> placed at 1
- find 66: probed 0, 1 -> found

Final table (cell index above, content below; `–` = empty, `DEL` = deleted):

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| 22 | 66 | 44 | 55 | 12 | – | – | – | – | – | – |

Now 66 reuses cell 1, `find 66` takes 2 probes instead of 6, and the table has no tombstone left.

**HW5 5.7b (professor's answer):** the variant has strong advantages when there are many insertions and deletions intermixed: available cells are found faster (earlier on the path), keys stay closer to their home, and the table fills with DELETED cells less - so rehashing due to "too many deleted elements" happens less often. It can be slower in other situations (extra bookkeeping per probe, no benefit when nothing was deleted). In general lazy deletion *is* implemented as 5.7 describes.

**Deleted cells and rehash.** The rehash trigger counts them, but the rehash re-inserts only ACTIVE cells:

Engine: `python tools/study.py hash run 14,21,-14,28,35,42 --size 7 --method quadratic --rehash`

- insert 14: hash = 14 mod 7 = 0 -> placed at 0
- insert 21: hash = 21 mod 7 = 0; collisions at 0; tried h0=0, h1=1 -> placed at 1
- remove 14: probed 0 -> found at 0, marked DELETED (lazy deletion)
- insert 28: hash = 28 mod 7 = 0; collisions at 0, 1; tried h0=0, h1=1, h2=4 -> placed at 4
- insert 35: hash = 35 mod 7 = 0; collisions at 0, 1, 4; tried h0=0, h1=1, h2=4, h3=2 -> placed at 2
  - *currentSize 4 > TableSize/2 = 3 -> rehash*
  - *REHASH: new TableSize = nextPrime(2*7) = 17; re-inserting [21, 35, 28] in old-table order with hash = x mod 17*
- insert 21: hash = 21 mod 17 = 4 -> placed at 4
- insert 35: hash = 35 mod 17 = 1 -> placed at 1
- insert 28: hash = 28 mod 17 = 11 -> placed at 11
- insert 42: hash = 42 mod 17 = 8 -> placed at 8

Final table (final TableSize 17) (cell index above, content below; `–` = empty, `DEL` = deleted):

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| – | 35 | – | – | 21 | – | – | – | 42 | – | – | 28 | – | – | – | – | – |

Only three keys are active after the removal, yet inserting 35 makes `currentSize = 4 > 7/2 = 3` and the table is rebuilt at size 17 without the tombstone.

### Check yourself
1. Linear probing, size 7: insert 7, 14, 21; remove 14; find 21. How many probes does the find take, and why does it not stop at the deleted cell?
2. With the textbook insert (not 5.7), where does the next key with home 0 go after those operations?

<details><summary>Answer</summary>

Engine log:

- insert 7: hash = 7 mod 7 = 0 -> placed at 0
- insert 14: hash = 14 mod 7 = 0; collisions at 0; tried h0=0, h1=1 -> placed at 1
- insert 21: hash = 21 mod 7 = 0; collisions at 0, 1; tried h0=0, h1=1, h2=2 -> placed at 2
- remove 14: probed 0, 1 -> found at 1, marked DELETED (lazy deletion)
- find 21: probed 0, 1, 2 -> found
- insert 28: hash = 28 mod 7 = 0; collisions at 0, 1, 2; tried h0=0, h1=1, h2=2, h3=3 -> placed at 3

1. The find takes **3 probes** (cells 0, 1, 2): cell 1 is DELETED, but a DELETED cell is not EMPTY and holds a different key, so the search continues past it and finds 21 at cell 2.
2. With the textbook insert (the next key with home 0, e.g. 28) probes 0, 1 (deleted: skipped), 2, then the first **EMPTY** cell 3 and is placed at 3; the tombstone at cell 1 stays. Final: `0:7 1:D 2:21 3:28`. (With the Exercise 5.7 variant 28 would reuse cell 1.)
</details>

---

## 6. Rehashing (textbook 5.5, Figs 5.19-5.22; HW5 5.2 and 5.4)

### 6.1 Worked example first: the book's Figs 5.19-5.21

Linear probing, size 7, `h(x) = x mod 7`. Insert 13, 15, 6, 24 -> Fig 5.19:

Engine: `python tools/study.py hash run 13,15,6,24 --size 7 --method linear`

- insert 13: hash = 13 mod 7 = 6 -> placed at 6
- insert 15: hash = 15 mod 7 = 1 -> placed at 1
- insert 6: hash = 6 mod 7 = 6; collisions at 6; tried h0=6, h1=0 -> placed at 0
- insert 24: hash = 24 mod 7 = 3 -> placed at 3

Final table (cell index above, content below; `–` = empty, `DEL` = deleted):

| 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| 6 | 15 | – | 24 | – | – | 13 |

Insert 23 (home 2) -> Fig 5.20 (the book calls this "over 70 percent full", 5/7). Build the new table: the first prime >= 2 * 7 = 14 is **17**; scan the old table in index order (6, 15, 23, 24, 13) and insert each with `x mod 17`:

Engine: `python tools/study.py hash run 6,15,23,24,13 --size 17 --method linear`

- insert 6: hash = 6 mod 17 = 6 -> placed at 6
- insert 15: hash = 15 mod 17 = 15 -> placed at 15
- insert 23: hash = 23 mod 17 = 6; collisions at 6; tried h0=6, h1=7 -> placed at 7
- insert 24: hash = 24 mod 17 = 7; collisions at 7; tried h0=7, h1=8 -> placed at 8
- insert 13: hash = 13 mod 17 = 13 -> placed at 13

Final table (cell index above, content below; `–` = empty, `DEL` = deleted):

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| – | – | – | – | – | – | 6 | 23 | 24 | – | – | – | – | 13 | – | 15 | – |

That is Fig 5.21 (6 at 6, 23 at 7 (collided with 6), 24 at 8 (collided with 23), 13 at 13, 15 at 15).

**Warning (textbook inconsistency):** the *code* of Fig 5.17 rehashes as soon as `currentSize > TableSize/2`, i.e. already when the 4th key (24) goes in, not on the 5th. The book's Fig 5.19-5.21 example just shows the mechanics. When the exam gives you a table, apply the code's threshold:

Engine: `python tools/study.py hash run 13,15,6,24,23 --size 7 --method linear --rehash`

- insert 13: hash = 13 mod 7 = 6 -> placed at 6
- insert 15: hash = 15 mod 7 = 1 -> placed at 1
- insert 6: hash = 6 mod 7 = 6; collisions at 6; tried h0=6, h1=0 -> placed at 0
- insert 24: hash = 24 mod 7 = 3 -> placed at 3
  - *currentSize 4 > TableSize/2 = 3 -> rehash*
  - *REHASH: new TableSize = nextPrime(2*7) = 17; re-inserting [6, 15, 24, 13] in old-table order with hash = x mod 17*
- insert 6: hash = 6 mod 17 = 6 -> placed at 6
- insert 15: hash = 15 mod 17 = 15 -> placed at 15
- insert 24: hash = 24 mod 17 = 7 -> placed at 7
- insert 13: hash = 13 mod 17 = 13 -> placed at 13
- insert 23: hash = 23 mod 17 = 6; collisions at 6, 7; tried h0=6, h1=7, h2=8 -> placed at 8

Final table (final TableSize 17) (cell index above, content below; `–` = empty, `DEL` = deleted):

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| – | – | – | – | – | – | 6 | 24 | 23 | – | – | – | – | 13 | – | 15 | – |

### 6.2 The rule

- **When:** probing: `++currentSize > TableSize/2`. Chaining: `++currentSize > TableSize`. (The book also allows rehashing only when an insertion fails, or at some chosen load factor; the code uses 0.5 for probing tables.)
- **To what:** `nextPrime(2 * oldSize)` - roughly double, and prime again. Ask: `nextPrime(14) = 17`, `nextPrime(22) = 23`, `nextPrime(10) = 11`, `nextPrime(20) = 23`. (`python tools/study.py hash prime N` prints it.)
- **How:** make a new empty table, then go through the **old table in index order** and `insert` every ACTIVE element (chaining: every node of every list, bucket 0 first, front to back) - the *new* hash function `x mod newSize` is used. The order matters for the final layout when there are collisions.
- **Why recompute rather than copy:** the hash value `x mod TableSize` depends on the table size, so every element's cell changes.
- DELETED cells are discarded.

```cpp
// Fig 5.22 - rehash for probing tables
void rehash( )
{
    vector<HashEntry> oldArray = array;

    // Create new double-sized, empty table
    array.resize( nextPrime( 2 * oldArray.size( ) ) );
    for( auto & entry : array )
        entry.info = EMPTY;

    // Copy table over
    currentSize = 0;
    for( auto & entry : oldArray )
        if( entry.info == ACTIVE )
            insert( std::move( entry.element ) );
}
```

Lines: copy the old array; `resize(nextPrime(2*oldSize))` makes the table bigger (new cells are default-constructed, then every `info` is set to EMPTY - including the surviving old cells, since `resize` keeps the old contents); `currentSize = 0` because `insert` will count the elements again; the loop re-inserts only `ACTIVE` entries (this drops DELETED ones), moving the element since the old copy is discarded. The chaining version is the same with `vector<list<HashedObj>>`, `clear()` on every list, and a double loop over the old lists. Note the re-insertion goes through the normal `insert`, so it uses `myhash` with the new table size.

### 6.3 HW5 5.2: "Show the result of rehashing the tables in 5.1" - only for 5.1c, with `x mod 23`

The 5.1c quadratic table was `0:9679 1:4371 3:1323 4:6173 5:4344 8:1989 9:4199`. Read it in index order: 9679, 4371, 1323, 6173, 4344, 1989, 4199. The new size is `nextPrime(2 * 10) = 23`; insert each key with `x mod 23` and quadratic probing:

Engine: `python tools/study.py hash run 9679,4371,1323,6173,4344,1989,4199 --size 23 --method quadratic`

- insert 9679: hash = 9679 mod 23 = 19 -> placed at 19
- insert 4371: hash = 4371 mod 23 = 1 -> placed at 1
- insert 1323: hash = 1323 mod 23 = 12 -> placed at 12
- insert 6173: hash = 6173 mod 23 = 9 -> placed at 9
- insert 4344: hash = 4344 mod 23 = 20 -> placed at 20
- insert 1989: hash = 1989 mod 23 = 11 -> placed at 11
- insert 4199: hash = 4199 mod 23 = 13 -> placed at 13

Final table (cell index above, content below; `–` = empty, `DEL` = deleted):

`1:4371 9:6173 11:1989 12:1323 13:4199 19:9679 20:4344`

(Each home cell: 9679 mod 23 = 19, 4371 mod 23 = 1, 1323 mod 23 = 12, 6173 mod 23 = 9, 4344 mod 23 = 20, 1989 mod 23 = 11, 4199 mod 23 = 13.) **No collisions** - the same result as the professor's sheet (`1:4371 9:6173 11:1989 12:1323 13:4199 19:9679 20:4344`).

### 6.4 More examples (engine-verified)

Quadratic, size 7, keys 9, 16, 23, 2, 30, 37:

Engine: `python tools/study.py hash run 9,16,23,2,30,37 --size 7 --method quadratic --rehash`

- insert 9: hash = 9 mod 7 = 2 -> placed at 2
- insert 16: hash = 16 mod 7 = 2; collisions at 2; tried h0=2, h1=3 -> placed at 3
- insert 23: hash = 23 mod 7 = 2; collisions at 2, 3; tried h0=2, h1=3, h2=6 -> placed at 6
- insert 2: hash = 2 mod 7 = 2; collisions at 2, 3, 6; tried h0=2, h1=3, h2=6, h3=4 -> placed at 4
  - *currentSize 4 > TableSize/2 = 3 -> rehash*
  - *REHASH: new TableSize = nextPrime(2*7) = 17; re-inserting [9, 16, 2, 23] in old-table order with hash = x mod 17*
- insert 9: hash = 9 mod 17 = 9 -> placed at 9
- insert 16: hash = 16 mod 17 = 16 -> placed at 16
- insert 2: hash = 2 mod 17 = 2 -> placed at 2
- insert 23: hash = 23 mod 17 = 6 -> placed at 6
- insert 30: hash = 30 mod 17 = 13 -> placed at 13
- insert 37: hash = 37 mod 17 = 3 -> placed at 3

Final table (final TableSize 17) (cell index above, content below; `–` = empty, `DEL` = deleted):

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| – | – | 2 | 37 | – | – | 23 | – | – | 9 | – | – | – | 30 | – | – | 16 |

Linear, size 11, keys 22, 33, 44, 55, 66, 77, 88, 5 (`11/2 = 5`, so the rehash comes on the 6th key):

Engine: `python tools/study.py hash run 22,33,44,55,66,77,88,5 --size 11 --method linear --rehash`

- insert 22: hash = 22 mod 11 = 0 -> placed at 0
- insert 33: hash = 33 mod 11 = 0; collisions at 0; tried h0=0, h1=1 -> placed at 1
- insert 44: hash = 44 mod 11 = 0; collisions at 0, 1; tried h0=0, h1=1, h2=2 -> placed at 2
- insert 55: hash = 55 mod 11 = 0; collisions at 0, 1, 2; tried h0=0, h1=1, h2=2, h3=3 -> placed at 3
- insert 66: hash = 66 mod 11 = 0; collisions at 0, 1, 2, 3; tried h0=0, h1=1, h2=2, h3=3, h4=4 -> placed at 4
- insert 77: hash = 77 mod 11 = 0; collisions at 0, 1, 2, 3, 4; tried h0=0, h1=1, h2=2, h3=3, h4=4, h5=5 -> placed at 5
  - *currentSize 6 > TableSize/2 = 5 -> rehash*
  - *REHASH: new TableSize = nextPrime(2*11) = 23; re-inserting [22, 33, 44, 55, 66, 77] in old-table order with hash = x mod 23*
- insert 22: hash = 22 mod 23 = 22 -> placed at 22
- insert 33: hash = 33 mod 23 = 10 -> placed at 10
- insert 44: hash = 44 mod 23 = 21 -> placed at 21
- insert 55: hash = 55 mod 23 = 9 -> placed at 9
- insert 66: hash = 66 mod 23 = 20 -> placed at 20
- insert 77: hash = 77 mod 23 = 8 -> placed at 8
- insert 88: hash = 88 mod 23 = 19 -> placed at 19
- insert 5: hash = 5 mod 23 = 5 -> placed at 5

Final table (final TableSize 23) (cell index above, content below; `–` = empty, `DEL` = deleted):

`5:5 8:77 9:55 10:33 19:88 20:66 21:44 22:22`

### 6.5 Cost: why it is cheap on average (book p.209)

- One rehash with N elements costs **O(N)** (N re-insertions into a table of size about 2N; the old table is scanned once).
- It happens only after the table doubled: "there must have been N/2 insertions prior to the last rehash", so the O(N) cost is spread over >= N/2 insertions: **a constant added to each insertion** -> amortized O(1) per insert. That is *why the new table is twice as large* (growing by a fixed amount would give O(N^2) total).
- A single unlucky insert still costs O(N) (the user "whose insertion caused a rehash" may notice a slowdown).

### 6.6 HW5 5.4: when to shrink?

Rule in the question: grow when the number of elements is twice the table size (chaining, lambda = 2). The professor's answer: a minimum load factor of around **0.5** works well (anything not too low and not too close to 1). Reason: after growing at lambda = 2 (doubling) the load factor is 1; after halving at load factor L the factor becomes 2L. If L were close to 1, halving would put lambda near 2 and we would immediately regrow ("rehash up and down too frequently"). With L = 0.5 the shrunk table has lambda = 1 - far from both thresholds. Also, "a maximum load factor of 2 is fairly reasonable with separate chaining (why is that?)": chains are then just 2 nodes long on average (successful search about 1 + 2/2 = 2), and nothing breaks as lambda grows (no probe sequences to exhaust).

### Check yourself
1. Probing table of size 11 currently holds 5 keys. What happens on the next insert? New size?
2. Chaining table of size 13 holds 13 keys. Insert one more. What happens?
3. What is the cost of one rehash with N elements, and why is insertion still O(1) amortized?

<details><summary>Answer</summary>

1. After the insert `currentSize = 6 > 11/2 = 5`, so rehash: new size nextPrime(22) = 23; the 6 keys are re-inserted in index order with `x mod 23`.
2. `++currentSize = 14 > 13`, so rehash to nextPrime(26) = 29 (chaining threshold lambda > 1).
3. O(N). It only happens after the number of elements has doubled, so the cost is shared by at least N/2 previous insertions: constant extra per insertion on average.
</details>

---

## 7. Expected number of probes / the load factor (textbook 5.3-5.4, high level)

**Chaining:** unsuccessful search = lambda nodes on average; successful = 1 + lambda/2 (section 3). Table size does not matter, load factor does.

**Linear probing** (with primary clustering; the book "does not perform the calculations"):

- insertion / unsuccessful search: `1/2 * (1 + 1/(1 - lambda)^2)` probes
- successful search: `1/2 * (1 + 1/(1 - lambda))` probes

**Random (no clustering) strategy** - what quadratic/double hashing approximate:

- insertion / unsuccessful: `1/(1 - lambda)` (a fraction 1 - lambda of cells are empty -> expect 1/(1-lambda) probes until an empty one)
- successful: `(1/lambda) * ln(1/(1 - lambda))` (average over the load factor the table had when each element was inserted)

| lambda | linear: insert | linear: successful | random: insert | random: successful | chaining: unsucc. | chaining: succ. |
|---|---|---|---|---|---|---|
| 0.50 | 2.5 | 1.50 | 2.0 | 1.39 | 0.50 | 1.25 |
| 0.75 | 8.5 | 2.50 | 4.0 | 1.85 | 0.75 | 1.38 |
| 0.90 | 50.5 | 5.50 | 10.0 | 2.56 | 0.90 | 1.45 |
| 1.00 | n/a (table too full) | n/a | n/a | n/a | 1.00 | 1.50 |
| 2.00 | n/a (table too full) | n/a | n/a | n/a | 2.00 | 2.00 |

The book quotes 2.5 / 1.5 probes at lambda = 0.5, 8.5 at 0.75 and 50 at 0.9 ("unreasonable") for linear probing, versus 4 and 10 without clustering. Conclusion in the book: linear probing is a bad idea if the table is expected to be more than half full; keep lambda < 0.5 for probing tables. For chaining lambda about 1 (up to 2 per the HW solution) is fine.

### Check yourself
1. Linear probing at lambda = 0.5: expected probes to insert? To find an existing key?
2. Chaining at lambda = 1.5: expected nodes in a successful search?

<details><summary>Answer</summary>

1. Insert: 1/2 (1 + 1/(0.5)^2) = 1/2 (1 + 4) = 2.5. Successful: 1/2 (1 + 1/0.5) = 1.5.
2. 1 + 1.5/2 = 1.75.
</details>

---

## 8. Hash tables in the standard library and what hashes cannot do (textbook 5.6, slides "Why Hash Maps?", HW5 5.12)

### 8.1 STL containers

- `unordered_set<T>`, `unordered_map<K,V>` (C++11): the hash-table versions of `set`/`map`. Elements/keys need **`operator==`** and a **hash function object**.
- The default `std::hash<T>` exists for ints, strings, ... For your own class, specialize `hash` (text p.198-199):

```cpp
class Employee
{
  public:
    const string & getName( ) const { return name; }
    bool operator==( const Employee & rhs ) const { return getName( ) == rhs.getName( ); }
    bool operator!=( const Employee & rhs ) const { return !( *this == rhs ); }
  private:
    string name; double salary; int seniority;
};

template<>
class hash<Employee>
{
  public:
    size_t operator()( const Employee & item )
    {
        static hash<string> hf;
        return hf( item.getName( ) );     // hash only the key part
    }
};
```

  The functor returns a raw `size_t`; the table itself reduces it (`myhash`: `hf(x) % theLists.size()`). Equal objects must hash equal, so hash exactly the members that `==` compares.
- Or pass the hash and equality as **template arguments** (Fig 5.23): `unordered_set<string, CaseInsensitiveStringHash, CaseInsensitiveStringHash> s;` where the class has `operator()(const string&)` (hash of the lower-cased string) and `operator()(const string&, const string&)` (equals-ignoring-case).
- Use them "if it is not important for the entries to be viewable in sorted order". The book's word-changing example: the maps keyed by word length and by representative can be `unordered_map`; the third map could be too unless the output must be alphabetical. "The performance of an unordered_map can often be superior to a map, but it is hard to know for sure without writing the code both ways."
- Costs (cplusplus.com): `insert`, `find`, `erase`, `operator[]`: **average O(1), worst O(n)**. Iterating all elements is O(n) (plus bucket count) - and in no useful order.

### 8.2 HW5 5.12: remembering the hash value

Rehashing recomputes every element's hash, which is costly for strings. Solution (professor): add a `size_t` private member to `Employee` and set it to the result of `hash<Employee>` the first time the object is hashed. When it stays valid: as long as the **name** (the hashed member) does not change. If you cache the *unscaled* `size_t` the functor returns (the `% TableSize` is applied afterwards by `myhash`) it survives a rehash; if what you stored was the *scaled table index*, a rehash changes it (this is the professor's remark: "difficult to use when rehashing, as rehashing normally would change all the hash values"). Also invalid when you change the hash function or the name.

### 8.3 Why hashes are not ordered - what you cannot do (slide "Why Hash Maps?")

| you want | hash (`unordered_set`) | balanced BST (`set`) |
|---|---|---|
| insert / erase / find | **O(1) avg**, O(n) worst | O(log n) worst |
| min / max / first / last | **no** (O(n) scan) | O(log n) (walk to the leftmost/rightmost node) |
| sorted iteration | **no** (sort a copy: O(n log n)) | O(n) in-order traversal |
| range query [a, b] | no (O(n) scan) | `lower_bound` / `upper_bound`, O(log n + k) |
| median, k-th smallest | no | O(k) walking from `begin` (no order-statistic tree in STL) |
| union / intersection ops | none built in | (`set_union` etc. on sorted ranges) |
| duplicates | not allowed (multiset by mapping value -> count) | `multiset` available |

The slide's summary: "O(1) insert, delete, and lookup. And nothing else." Therefore hashes are *not* good for numeric data where you want order/range/aggregate queries. What they are good for: records with unique identifiers (id -> record = the main practical use), sets used mostly for insert/delete/lookup, multisets as value -> count, and string/sequence problems (last-seen position of a character, duplicates within a window). Iterating a hash is O(n) as long as the load factor is kept at a minimum.

### 8.4 The classic slide problem: do two integers in an array add up to x?

| approach | time | extra space |
|---|---|---|
| naive: all pairs | O(n^2) | O(1) |
| sort, then two pointers from both ends | O(n log n) (sort) + O(n) | O(1) |
| hash: for each a, look for x - a in an `unordered_set`, then insert a | **O(n) average**, O(n^2) worst | O(n) |

### Check yourself
1. What two things must a user-defined key type provide to be stored in an `unordered_set`?
2. You need "all values between 10 and 20" from a set of n numbers (k results). Hash or tree, and what cost?
3. State the cost of `unordered_map::find` in both cases.

<details><summary>Answer</summary>

1. `operator==` (equality) and a `hash<T>` function object (or custom hash/equality functors passed as template arguments).
2. Tree (`set`): `lower_bound(10)` to `upper_bound(20)`, O(log n + k). A hash would have to scan everything: O(n).
3. Average O(1), worst case O(n) (everything in one bucket / one probe cluster).
</details>

---

## 9. Complexity table (average vs worst) - say both every time

N elements, load factor kept O(1), reasonable hash function. (Weiss text for the structure; cplusplus.com for STL.)

| operation | chaining (avg) | probing (avg) | **worst case** | reason |
|---|---|---|---|---|
| insert | O(1) amortized | O(1) amortized | O(N) | duplicate check scans the list/cluster; an insert that triggers a rehash is O(N) |
| find / contains | O(1) (about 1 + lambda/2 nodes) | O(1) (1/(1-lambda) probes) | O(N) | all keys in one bucket / one cluster |
| remove | O(1) | O(1) (lazy) | O(N) | find, then erase / mark |
| rehash | O(N) | O(N) | O(N) | re-insert N elements into a table of size about 2N |
| min / max / sorted / range | O(N) (scan) | O(N) | O(N) | no order |
| iterate all | O(N + TableSize) = O(N) | O(N + TableSize) | O(N) | visit every cell |
| space | O(N + TableSize) | O(TableSize) >= 2N | | probing needs a bigger table |
| hash of a string key | O(length) | | | included in the "O(1)" if keys are short (the professor's DNA answer: "expensive O(1)") |

**n insertions** into an initially small table with doubling rehash: total **O(n) average** (amortized O(1) each), O(n^2) worst (every key in one bucket). Chaining and probing are both O(n) per operation in that worst case; replacing the lists with balanced trees would cap it at O(log n).

**Hash tables vs BSTs (chapter objective):** hash: faster on average, no order. BST (`set`/`map`): O(log n) *worst*, ordered, range queries, in-order traversal, successor/predecessor.

---

## 10. Traps that cost points

1. **Chain order.** New key is appended at the **end** of the list, not the front (Fig 5.5 draws it at the front - ignore).
2. **Quadratic probes are `+1, +4, +9`, not `+1, +2, +3`**; the *home* cell is probe 0. Always reduce mod TableSize at every step (`9 + 9 = 18 -> 8` in a size-10 table).
3. **Double hashing:** `hash2(x) = R - (x mod R)`, with the *R given* (HW: 7), not `x mod R`. Probe i is `home + i * hash2(x)`, reduced mod TableSize. If the problem's table size is not prime, "cannot place" can happen early (HW5 5.1d).
4. **"Cannot place"** = TableSize probes without finding an EMPTY cell. State the cells you tried.
5. **Rehash thresholds differ:** probing `> TableSize/2` after the insert (7 -> rehash when the 4th key goes in), chaining `> TableSize`. The key that triggered the rehash **is already in the table** and is moved with the others (it is not inserted a second time afterwards).
6. **Rehash order:** old table in index order, new hash `x mod newSize`, new size **nextPrime(2 * old)** (11 -> 23, 7 -> 17, 5 -> 11, 10 -> 23).
7. **Lazy deletion:** do not stop at a DELETED cell during find; DELETED still counts toward `currentSize`; a plain insert uses the first EMPTY cell (not the tombstone) unless the question says Exercise 5.7.
8. **Collisions are between cells, not just between equal hash values:** in linear probing a key with home 4 can collide with a key that was pushed into cell 4.
9. **Average vs worst:** hash operations are O(1) *average*, O(n) *worst*; saying only "O(1)" loses the case-analysis credit. Strings: the hash itself costs O(length).
10. **A hash cannot give min/max/sorted/range** - never use `unordered_set` where the solution needs order. (And `std::set` is O(log n), not O(1).)
11. **Load factor** is elements / TableSize, not elements / "occupied cells"; probing needs lambda <= 0.5, chaining lambda about 1.
12. **Fig 5.2 hash of anagrams collide**; Fig 5.3 uses only the first three characters; Fig 5.4 is the good one but the slowest.

---

## 11. What the exam asks (and mini quick-reference)

| likely question | where in this file | what a full answer contains |
|---|---|---|
| "Insert these keys into a size-N table using X; show the table" | 3-4 | per-key home cell, probe list for collisions, final table; for double hashing show hash2 |
| "Show the result of rehashing" | 6 | new size nextPrime(2N), old index order, new home cells, final table |
| lazy-deletion trace with finds | 5 | probe list per op, DELETED markers, where the next insert goes |
| "Why must the table size be prime?" | 2.1, 4.3, 4.4 | multiples of the table size / skipped cells / quadratic reaches only half the cells (Theorem 5.1) / double hashing steps cycle all cells |
| "Why lambda <= 0.5 for probing but about 1 for chaining?" | 4, 7 | clustering and the probe formulas; chaining has no probe sequence to exhaust |
| clustering | 4.1-4.2 | primary (linear) vs secondary (quadratic); double hashing avoids both |
| hash container in a complexity/coding question | 8, 9 | per-operation average O(1), worst O(n); string hash cost; no order |

Checklist for a hash trace on the exam: (1) write `hash(x) = x mod TableSize` and the probe formula; (2) compute every home cell first; (3) place keys strictly in the given order; (4) write the cells you tried for each collision; (5) check the load factor against the rehash threshold after each insert; (6) draw the final table with all TableSize cells numbered.
