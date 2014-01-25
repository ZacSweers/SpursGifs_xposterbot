SpursGifs_xposterbot
====================

Reddit bot I started writing while sitting bored in a hotel room for x-posting gifs/vines/gyfcats from /r/coys to /r/SpursGifs.

# Basic flow
- Runs on Heroku, using the free scheduler. Checking once/hour for now.
- Xposts to /r/SpursGifs (converts to gfycat first if it's a gif or vine)
- Comments on the new post giving credit to the OP
- Comments on the original post linking the x-posted submission

# TODO
* ~~Use a DB on heroku for caching there (local pickle file doesn't persist between runs)~~ Done!
* ~~Convert gifs to gfycat~~ Done!
* ~~Cache previously gfycat'd urls.~~ Done!
* ~~Use gfycat's API for checking to see if a gif was already converted. Minor, and I think their API already does this server-side~~ Not necessary, they handle this already internally.
* ~~Convert Vine videos to gfycat (for consistency/convenience)~~ Done!


## License

     The MIT License (MIT)

	 Copyright (c) 2014 Henri Sweers

	 Permission is hereby granted, free of charge, to any person obtaining a copy of
	 this software and associated documentation files (the "Software"), to deal in
	 the Software without restriction, including without limitation the rights to
	 use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
	 the Software, and to permit persons to whom the Software is furnished to do so,
	 subject to the following conditions:

	 The above copyright notice and this permission notice shall be included in all
	 copies or substantial portions of the Software.

	 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
	 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
	 FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
	 COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
	 IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
	 CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.