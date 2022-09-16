/*
 * Copyright (c) 2021, TU Dresden.
 *
 * Redistribution and use in source and binary forms, with or without modification,
 * are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
 * EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
 * THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
 * THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 * @author Johannes Hayeß
 */

use std::ops::Deref;
use std::os::raw::c_long;

pub struct RandomValue(c_long);

// We use c_long to ensure compatibility with the C++ version.
pub struct PseudoRandomGenerator {
    m: c_long,
}

impl PseudoRandomGenerator {
    /// Reset internal state, as if this was just created with given seed.
    pub fn reseed(&mut self, seed: c_long) {
        self.m = seed;
    }

    pub fn next(&mut self) -> RandomValue {
        self.m = ((self.m * 1309) + 13849) & 65535;
        RandomValue(self.m)
    }

    pub fn next_in_range(&mut self, range: std::ops::Range<c_long>) -> RandomValue {
        let x = *(self.next());
        RandomValue(range.start + (x % (range.end - range.start)))
    }
}

impl Default for PseudoRandomGenerator {
    fn default() -> Self {
        PseudoRandomGenerator::from(74755)
    }
}

impl From<c_long> for PseudoRandomGenerator {
    fn from(seed: c_long) -> Self {
        PseudoRandomGenerator { m: seed }
    }
}

impl Deref for RandomValue {
    type Target = c_long;

    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

impl Into<i32> for RandomValue {
    fn into(self) -> i32 {
        *self as i32
    }
}

impl Into<u32> for RandomValue {
    fn into(self) -> u32 {
        *self as u32
    }
}

impl Into<u64> for RandomValue {
    fn into(self) -> u64 {
        *self as u64
    }
}

impl Into<usize> for RandomValue {
    fn into(self) -> usize {
        *self as usize
    }
}

impl Into<f64> for RandomValue {
    fn into(self) -> f64 {
        1.0 / ((*self + 1) as f64)
    }
}
